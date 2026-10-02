"""Phase 5 knowledge persistence tests."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import uuid

from pydantic import HttpUrl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sentinel.db.models import (
    Base,
    CompanyORM,
    MarketEventORM,
    OrganizationORM,
    PersonORM,
    ThemeORM,
)
from sentinel.db.repository import (
    ArticleRepository,
    CompanyRepository,
    KnowledgeRepository,
    MarketEventRepository,
    OrganizationRepository,
    PersonRepository,
    SourceRepository,
    ThemeRepository,
)
from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    EventSeverity,
    MarketRegion,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
)
from sentinel_core.models import Article, Company, MarketEvent, Organization, Person, Source, Theme


@pytest.fixture()
def session_local():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False, future=True
    )
    yield session_factory
    engine.dispose()


@pytest.mark.unit
def test_typed_knowledge_round_trip_and_exact_name_idempotency(session_local) -> None:
    company_repo = CompanyRepository(lambda: session_local())
    person_repo = PersonRepository(lambda: session_local())
    organization_repo = OrganizationRepository(lambda: session_local())
    theme_repo = ThemeRepository(lambda: session_local())

    company = Company(name="Apple Inc.")
    saved_company = company_repo.save_company(company)
    duplicate_company = company_repo.save_company(Company(name="Apple Inc."))
    assert saved_company.id == duplicate_company.id

    person = Person(full_name="Jerome Powell")
    saved_person = person_repo.save_person(person)
    duplicate_person = person_repo.save_person(Person(full_name="Jerome Powell"))
    assert saved_person.id == duplicate_person.id

    organization = Organization(name="Federal Reserve System")
    saved_organization = organization_repo.save_organization(organization)
    duplicate_organization = organization_repo.save_organization(
        Organization(name="Federal Reserve System")
    )
    assert saved_organization.id == duplicate_organization.id

    theme = Theme(name="AI Capex Cycle", slug="ai-capex-cycle")
    saved_theme = theme_repo.save_theme(theme)
    duplicate_theme = theme_repo.save_theme(Theme(name="AI Capex Cycle", slug="ai-capex-cycle"))
    assert saved_theme.id == duplicate_theme.id

    with session_local() as session:
        company_row = session.get(CompanyORM, str(saved_company.id))
        person_row = session.get(PersonORM, str(saved_person.id))
        theme_row = session.get(ThemeORM, str(saved_theme.id))
        assert company_row is not None
        assert person_row is not None
        assert theme_row is not None
        assert company_row.name == "Apple Inc."
        assert person_row.name == "Jerome Powell"
        assert person_row.to_domain().full_name == person.full_name
        assert (
            session.get(OrganizationORM, str(saved_organization.id)).name
            == "Federal Reserve System"
        )
        assert theme_row.name == "AI Capex Cycle"
        assert theme_row.to_domain().slug == theme.slug

        assert session.query(CompanyORM).filter_by(name="Apple Inc.").count() == 1
        assert session.query(PersonORM).filter_by(name="Jerome Powell").count() == 1
        assert session.query(OrganizationORM).filter_by(name="Federal Reserve System").count() == 1
        assert session.query(ThemeORM).filter_by(name="AI Capex Cycle").count() == 1


@pytest.mark.unit
def test_theme_with_non_derived_slug_cannot_be_round_tripped() -> None:
    theme = Theme(name="Artificial Intelligence", slug="ai")

    with pytest.raises(ValueError, match="Arbitrary Theme slug persistence is outside"):
        ThemeORM.from_domain(theme)


@pytest.mark.unit
def test_market_event_knowledge_relationships_round_trip(session_local) -> None:
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    company_repo = CompanyRepository(lambda: session_local())
    person_repo = PersonRepository(lambda: session_local())
    organization_repo = OrganizationRepository(lambda: session_local())
    theme_repo = ThemeRepository(lambda: session_local())
    market_repo = MarketEventRepository(lambda: session_local())
    knowledge_repo = KnowledgeRepository(lambda: session_local())

    source = source_repo.save_source(
        Source(
            name="Fed Watch",
            url=HttpUrl("https://example.com/fed-watch"),
            source_type=SourceType.RSS,
            status=SourceStatus.ACTIVE,
            region=MarketRegion.US,
            asset_class=AssetClass.MACRO,
            language="en",
            weight=1.0,
            fetch_interval_minutes=60,
        )
    )

    article_one = article_repo.save_article(
        Article(
            source_id=source.id,
            title="Fed holds rates steady",
            url=HttpUrl("https://example.com/fed-holds-rates"),
            content="The central bank kept rates steady as inflation remained elevated.",
            summary="The bank held rates steady.",
            published_at=None,
            fetched_at=datetime.now(tz=UTC),
            language="en",
            status=ArticleStatus.PROCESSED,
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            sector=Sector.FINANCIALS,
            content_hash=hashlib.sha256(b"fed-rates").hexdigest(),
        )
    )
    article_two = article_repo.save_article(
        Article(
            source_id=source.id,
            title="Treasury yields rise after rate signal",
            url=HttpUrl("https://example.com/treasury-yields"),
            content="Bond yields rose after the central bank signal.",
            summary="Bond yields rose.",
            published_at=None,
            fetched_at=datetime.now(tz=UTC),
            language="en",
            status=ArticleStatus.PROCESSED,
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            sector=Sector.FINANCIALS,
            content_hash=hashlib.sha256(b"treasury-yields").hexdigest(),
        )
    )

    company = company_repo.save_company(Company(name="Apple Inc."))
    person = person_repo.save_person(Person(full_name="Jerome Powell"))
    organization = organization_repo.save_organization(Organization(name="Federal Reserve System"))
    theme = theme_repo.save_theme(Theme(name="AI Capex Cycle", slug="ai-capex-cycle"))

    event = MarketEvent(
        title="Fed policy path stays restrictive",
        summary=(
            "The Federal Reserve signaled a higher-for-longer path for rates, with inflation "
            "still elevated and markets pricing a slower path to easing. The stance is "
            "important because it affects borrowing costs, bond yields, and the broader "
            "macroeconomic backdrop across US financial markets."
        ),
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        sector=Sector.FINANCIALS,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.NEUTRAL,
        sentiment_confidence=0.8,
        importance_score=8.1,
        importance_confidence=0.85,
        occurred_at=datetime.now(tz=UTC),
    )
    saved_event = market_repo.save_market_event(
        event, source_article_ids=[article_one.id, article_two.id]
    )
    knowledge_repo.save_market_event_knowledge(
        market_event_id=saved_event.id,
        company_ids=[company.id],
        person_ids=[person.id],
        organization_ids=[organization.id],
        theme_ids=[theme.id],
    )
    knowledge_repo.save_market_event_knowledge(
        market_event_id=saved_event.id,
        company_ids=[company.id],
        person_ids=[person.id],
        organization_ids=[organization.id],
        theme_ids=[theme.id],
    )

    with session_local() as session:
        event_row = session.get(MarketEventORM, str(saved_event.id))
        assert event_row is not None
        assert {uuid.UUID(row.id) for row in event_row.companies} == {company.id}
        assert {uuid.UUID(row.id) for row in event_row.people} == {person.id}
        assert {uuid.UUID(row.id) for row in event_row.organizations} == {organization.id}
        assert {uuid.UUID(row.id) for row in event_row.themes} == {theme.id}
        assert {uuid.UUID(row.id) for row in event_row.articles} == {article_one.id, article_two.id}

        assert len(event_row.companies) == 1
        assert len(event_row.people) == 1
        assert len(event_row.organizations) == 1
        assert len(event_row.themes) == 1


@pytest.mark.unit
def test_missing_market_event_and_entity_references_fail_without_partial_state(
    session_local,
) -> None:
    market_repo = MarketEventRepository(lambda: session_local())
    knowledge_repo = KnowledgeRepository(lambda: session_local())

    event = MarketEvent(
        title="Policy path stays restrictive",
        summary=(
            "Rates remain elevated and the policy path appears more restrictive than markets "
            "had expected, which matters for growth expectations, bond yields, and the "
            "overall macro backdrop across the US economy."
        ),
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        sector=Sector.FINANCIALS,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.NEUTRAL,
        sentiment_confidence=0.75,
        importance_score=7.5,
        importance_confidence=0.8,
        occurred_at=datetime.now(tz=UTC),
    )

    with pytest.raises(ValueError, match="does not exist"):
        knowledge_repo.save_market_event_knowledge(
            market_event_id=uuid.uuid4(),
            company_ids=[uuid.uuid4()],
        )

    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    source = source_repo.save_source(
        Source(
            name="Fed Watch",
            url=HttpUrl("https://example.com/fed-watch-failure"),
            source_type=SourceType.RSS,
            status=SourceStatus.ACTIVE,
            region=MarketRegion.US,
            asset_class=AssetClass.MACRO,
            language="en",
            weight=1.0,
            fetch_interval_minutes=60,
        )
    )
    article = article_repo.save_article(
        Article(
            source_id=source.id,
            title="Fed keeps policy stance steady",
            url=HttpUrl("https://example.com/fed-policy-stance"),
            content="The central bank continues to signal a restrictive policy path for rates.",
            summary="The central bank continues to signal a restrictive policy path for rates.",
            published_at=None,
            fetched_at=datetime.now(tz=UTC),
            language="en",
            status=ArticleStatus.PROCESSED,
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            sector=Sector.FINANCIALS,
            content_hash=hashlib.sha256(b"fed-policy-stance").hexdigest(),
        )
    )
    persisted_event = market_repo.save_market_event(event, source_article_ids=[article.id])

    with pytest.raises(ValueError, match="Company"):
        knowledge_repo.save_market_event_knowledge(
            market_event_id=persisted_event.id,
            company_ids=[uuid.uuid4()],
        )

    with session_local() as session:
        event_row = session.get(MarketEventORM, str(persisted_event.id))
        assert event_row is not None
        assert len(event_row.companies) == 0
        assert len(event_row.people) == 0
        assert len(event_row.organizations) == 0
        assert len(event_row.themes) == 0


@pytest.mark.unit
def test_phase5_relationships_are_deterministic_and_safe(session_local) -> None:
    company_repo = CompanyRepository(lambda: session_local())
    person_repo = PersonRepository(lambda: session_local())
    organization_repo = OrganizationRepository(lambda: session_local())
    theme_repo = ThemeRepository(lambda: session_local())
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    market_repo = MarketEventRepository(lambda: session_local())
    knowledge_repo = KnowledgeRepository(lambda: session_local())

    company = company_repo.save_company(Company(name="Microsoft"))
    person = person_repo.save_person(Person(full_name="Nina Patel"))
    organization = organization_repo.save_organization(Organization(name="SEC"))
    theme = theme_repo.save_theme(
        Theme(name="Private Credit Expansion", slug="private-credit-expansion")
    )

    source = source_repo.save_source(
        Source(
            name="Macro Monitor",
            url=HttpUrl("https://example.com/macro-monitor"),
            source_type=SourceType.RSS,
            status=SourceStatus.ACTIVE,
            region=MarketRegion.US,
            asset_class=AssetClass.MACRO,
            language="en",
            weight=1.0,
            fetch_interval_minutes=60,
        )
    )
    article = article_repo.save_article(
        Article(
            source_id=source.id,
            title="Risk markets remain constructive",
            url=HttpUrl("https://example.com/risk-markets"),
            content="Risk markets remain constructive after policy signals.",
            summary="Risk markets remain constructive.",
            published_at=None,
            fetched_at=datetime.now(tz=UTC),
            language="en",
            status=ArticleStatus.PROCESSED,
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            sector=Sector.FINANCIALS,
            content_hash=hashlib.sha256(b"risk-markets").hexdigest(),
        )
    )
    event = market_repo.save_market_event(
        MarketEvent(
            title="Private credit expansion strengthens",
            summary=(
                "The private credit backdrop remains constructive as capital continues to flow "
                "into financing activity and structured lender risk appetite stays resilient. "
                "This matters for credit conditions, corporate financing, and the broader "
                "risk environment across the US market."
            ),
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            sector=Sector.FINANCIALS,
            severity=EventSeverity.MEDIUM,
            sentiment=Sentiment.BULLISH,
            sentiment_confidence=0.72,
            importance_score=6.8,
            importance_confidence=0.8,
            occurred_at=datetime.now(tz=UTC),
        ),
        source_article_ids=[article.id],
    )

    knowledge_repo.save_market_event_knowledge(
        market_event_id=event.id,
        company_ids=[company.id, company.id],
        person_ids=[person.id, person.id],
        organization_ids=[organization.id, organization.id],
        theme_ids=[theme.id, theme.id],
    )
    knowledge_repo.save_company_theme_links(company_id=company.id, theme_ids=[theme.id])
    knowledge_repo.save_company_person_links(company_id=company.id, person_ids=[person.id])
    knowledge_repo.save_person_organization_links(
        person_id=person.id,
        organization_ids=[organization.id],
    )

    with session_local() as session:
        event_row = session.get(MarketEventORM, str(event.id))
        assert event_row is not None
        assert len(event_row.companies) == 1
        assert len(event_row.people) == 1
        assert len(event_row.organizations) == 1
        assert len(event_row.themes) == 1

    added_company = company_repo.save_company(Company(name="Nvidia"))
    added_person = person_repo.save_person(Person(full_name="Jensen Huang"))
    added_organization = organization_repo.save_organization(Organization(name="Federal Reserve"))
    added_theme = theme_repo.save_theme(Theme(name="AI Infrastructure", slug="ai-infrastructure"))

    for _ in range(2):
        knowledge_repo.save_market_event_knowledge(
            market_event_id=event.id,
            company_ids=[added_company.id],
            person_ids=[added_person.id],
            organization_ids=[added_organization.id],
            theme_ids=[added_theme.id],
        )
        knowledge_repo.save_company_theme_links(
            company_id=company.id,
            theme_ids=[added_theme.id],
        )
        knowledge_repo.save_company_person_links(
            company_id=company.id,
            person_ids=[added_person.id],
        )
        knowledge_repo.save_person_organization_links(
            person_id=person.id,
            organization_ids=[added_organization.id],
        )

    with session_local() as session:
        event_row = session.get(MarketEventORM, str(event.id))
        company_row = session.get(CompanyORM, str(company.id))
        person_row = session.get(PersonORM, str(person.id))
        assert event_row is not None
        assert company_row is not None
        assert person_row is not None
        assert {row.id for row in event_row.companies} == {
            str(company.id),
            str(added_company.id),
        }
        assert {row.id for row in event_row.people} == {
            str(person.id),
            str(added_person.id),
        }
        assert {row.id for row in event_row.organizations} == {
            str(organization.id),
            str(added_organization.id),
        }
        assert {row.id for row in event_row.themes} == {str(theme.id), str(added_theme.id)}
        assert {row.id for row in company_row.themes} == {str(theme.id), str(added_theme.id)}
        assert {row.id for row in company_row.people} == {str(person.id), str(added_person.id)}
        assert {row.id for row in person_row.organizations} == {
            str(organization.id),
            str(added_organization.id),
        }

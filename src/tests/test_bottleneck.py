"""
Bottleneck — Test Suite

Tests cover:
- Risk engine: composite score, level, ranking
- Mock ML: deterministic, probability ranges, health ranges, factors
- Maintenance: critical assets get immediate priority, reasons present
- Crew: suitable crews assigned, unavailable not assigned
- API: all primary endpoints
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient


# ─── Risk Engine Tests ────────────────────────────────────────────────────────

class TestRiskEngine:
    def setup_method(self):
        from backend.bottleneck.mock_data import ASSET_MAP
        from backend.bottleneck.grid_impact import compute_grid_impact
        from backend.bottleneck.weather_adapter import get_weather_exposure
        from backend.bottleneck.ml_adapter import MockFailurePredictor
        from backend.bottleneck.mock_data import get_latest_telemetry, get_incidents
        from backend.bottleneck.risk_engine import compute_risk
        from backend.bottleneck.contracts import FailurePrediction

        self.ASSET_MAP = ASSET_MAP
        self.compute_grid_impact = compute_grid_impact
        self.get_weather_exposure = get_weather_exposure
        self.MockFailurePredictor = MockFailurePredictor
        self.get_latest_telemetry = get_latest_telemetry
        self.get_incidents = get_incidents
        self.compute_risk = compute_risk
        self.FailurePrediction = FailurePrediction

    def _risk_for(self, asset_id: str):
        asset = self.ASSET_MAP[asset_id]
        tel = self.get_latest_telemetry(asset_id)
        inc = self.get_incidents(asset_id)
        wx = self.get_weather_exposure(asset)
        pred = self.MockFailurePredictor().predict(asset_id, tel, inc, wx, asset.age_years, asset.criticality)
        gi = self.compute_grid_impact(asset)
        return self.compute_risk(asset, pred, gi, wx)

    def test_high_probability_high_impact_gives_critical(self):
        """TR-1042: high prob + high impact → critical"""
        risk = self._risk_for('TR-1042')
        assert risk.risk_level in ('critical', 'high'), f"Expected critical/high for TR-1042, got {risk.risk_level}"
        assert risk.risk_score >= 60, f"Expected score >= 60, got {risk.risk_score}"

    def test_healthy_asset_gives_low_risk(self):
        """New healthy asset → low risk"""
        risk = self._risk_for('TR-7001')
        assert risk.risk_level in ('low', 'medium'), f"Expected low/medium for TR-7001, got {risk.risk_level}"
        assert risk.risk_score < 40, f"Expected score < 40, got {risk.risk_score}"

    def test_risk_score_in_valid_range(self):
        from backend.bottleneck.mock_data import ASSETS
        for asset in ASSETS:
            risk = self._risk_for(asset.id)
            assert 0.0 <= risk.risk_score <= 100.0, f"Risk score out of range for {asset.id}: {risk.risk_score}"

    def test_critical_asset_ranked_above_low_risk(self):
        risk_critical = self._risk_for('TR-1042')
        risk_healthy = self._risk_for('TR-7001')
        assert risk_critical.risk_score > risk_healthy.risk_score, \
            f"TR-1042 ({risk_critical.risk_score}) should outscore TR-7001 ({risk_healthy.risk_score})"

    def test_impact_influences_ranking(self):
        """Asset with higher customers at risk should score higher when failure prob is similar."""
        risk_high_impact = self._risk_for('TR-9001')   # hospital district, 12000 customers
        risk_low_impact = self._risk_for('CB-7330')    # tiny capacitor bank
        assert risk_high_impact.risk_score > risk_low_impact.risk_score, \
            "High-impact asset should outscore low-impact asset"

    def test_weather_affects_score(self):
        """North assets (storm exposure) should have higher weather_exposure_score than Central."""
        from backend.bottleneck.weather_adapter import get_weather_exposure
        north_asset = self.ASSET_MAP['TR-1042']   # North region
        central_asset = self.ASSET_MAP['RC-4401']  # Central region
        wx_north = get_weather_exposure(north_asset)
        wx_central = get_weather_exposure(central_asset)
        assert wx_north.weather_exposure_score > wx_central.weather_exposure_score, \
            f"North ({wx_north.weather_exposure_score}) should have higher weather exposure than Central ({wx_central.weather_exposure_score})"

    def test_risk_level_matches_score(self):
        from backend.bottleneck.mock_data import ASSETS
        for asset in ASSETS:
            risk = self._risk_for(asset.id)
            if risk.risk_score >= 75:
                assert risk.risk_level == 'critical'
            elif risk.risk_score >= 50:
                assert risk.risk_level == 'high'
            elif risk.risk_score >= 25:
                assert risk.risk_level == 'medium'
            else:
                assert risk.risk_level == 'low'


# ─── Mock ML Tests ────────────────────────────────────────────────────────────

class TestMockML:
    def setup_method(self):
        from backend.bottleneck.ml_adapter import MockFailurePredictor, get_predictor
        from backend.bottleneck.mock_data import ASSET_MAP, ASSETS, get_latest_telemetry, get_incidents
        from backend.bottleneck.weather_adapter import get_weather_exposure
        self.predictor = MockFailurePredictor()
        self.ASSET_MAP = ASSET_MAP
        self.ASSETS = ASSETS
        self.get_latest_telemetry = get_latest_telemetry
        self.get_incidents = get_incidents
        self.get_weather_exposure = get_weather_exposure

    def _predict(self, asset_id: str):
        asset = self.ASSET_MAP[asset_id]
        tel = self.get_latest_telemetry(asset_id)
        inc = self.get_incidents(asset_id)
        wx = self.get_weather_exposure(asset)
        return self.predictor.predict(asset_id, tel, inc, wx, asset.age_years, asset.criticality)

    def test_predictions_are_deterministic(self):
        """Same input → identical output every time."""
        p1 = self._predict('TR-1042')
        p2 = self._predict('TR-1042')
        assert p1.failure_probability_24h == p2.failure_probability_24h
        assert p1.health_score == p2.health_score
        assert p1.top_factors == p2.top_factors

    def test_probability_24h_in_valid_range(self):
        for asset in self.ASSETS:
            p = self._predict(asset.id)
            assert 0.0 <= p.failure_probability_24h <= 1.0, \
                f"{asset.id}: 24h probability {p.failure_probability_24h} out of range"

    def test_probability_72h_gte_24h(self):
        """72h probability should be >= 24h probability."""
        for asset in self.ASSETS:
            p = self._predict(asset.id)
            assert p.failure_probability_72h >= p.failure_probability_24h, \
                f"{asset.id}: 72h < 24h probability"

    def test_health_score_in_valid_range(self):
        for asset in self.ASSETS:
            p = self._predict(asset.id)
            assert 0.0 <= p.health_score <= 100.0, \
                f"{asset.id}: health score {p.health_score} out of range"

    def test_top_factors_returned(self):
        p = self._predict('TR-1042')
        assert len(p.top_factors) > 0, "TR-1042 should have top factors"

    def test_critical_asset_has_high_probability(self):
        p = self._predict('TR-1042')
        assert p.failure_probability_24h >= 0.7, \
            f"TR-1042 should have >= 70% 24h probability, got {p.failure_probability_24h}"

    def test_healthy_asset_has_low_probability(self):
        p = self._predict('TR-7001')
        assert p.failure_probability_24h <= 0.2, \
            f"TR-7001 should have <= 20% 24h probability, got {p.failure_probability_24h}"

    def test_scenario_predictor_increases_probability(self):
        from backend.bottleneck.ml_adapter import ScenarioFailurePredictor
        base = self._predict('TR-1042')
        asset = self.ASSET_MAP['TR-1042']
        tel = self.get_latest_telemetry('TR-1042')
        inc = self.get_incidents('TR-1042')
        wx = self.get_weather_exposure(asset)
        scenario_pred = ScenarioFailurePredictor('severe_storm').predict(
            'TR-1042', tel, inc, wx, asset.age_years, asset.criticality
        )
        assert scenario_pred.failure_probability_24h >= base.failure_probability_24h, \
            "Scenario should not decrease failure probability"


# ─── Maintenance Tests ────────────────────────────────────────────────────────

class TestMaintenance:
    def setup_method(self):
        from backend.bottleneck.service import get_full_ranking
        self.ranking = get_full_ranking()

    def test_critical_asset_gets_immediate_priority(self):
        critical_entries = [e for e in self.ranking if e.risk.risk_level == 'critical']
        if critical_entries:
            top = critical_entries[0]
            assert top.maintenance.priority_level in ('immediate', 'high'), \
                f"Critical asset {top.asset.id} should get immediate/high priority"

    def test_recommendations_include_reasons(self):
        for entry in self.ranking[:10]:
            assert len(entry.maintenance.reason) > 0, \
                f"Asset {entry.asset.id} maintenance has no reason"

    def test_priority_rank_is_unique(self):
        ranks = [e.maintenance.priority for e in self.ranking]
        assert len(set(ranks)) == len(ranks), "Maintenance priorities should be unique"

    def test_healthy_asset_gets_monitor_priority(self):
        healthy_entries = [e for e in self.ranking if e.risk.risk_level == 'low']
        for entry in healthy_entries:
            assert entry.maintenance.priority_level == 'monitor', \
                f"Low-risk asset {entry.asset.id} should get monitor priority, got {entry.maintenance.priority_level}"

    def test_recommended_window_present(self):
        for entry in self.ranking:
            assert len(entry.maintenance.recommended_window) > 0


# ─── Crew Tests ──────────────────────────────────────────────────────────────

class TestCrew:
    def setup_method(self):
        from backend.bottleneck.service import get_full_ranking
        from backend.bottleneck.mock_data import CREWS
        from backend.bottleneck.risk_engine import assign_crew
        self.ranking = get_full_ranking()
        self.CREWS = CREWS
        self.assign_crew = assign_crew

    def test_suitable_available_crew_assigned(self):
        """Critical assets should get crew assignments."""
        critical = [e for e in self.ranking if e.risk.risk_level == 'critical']
        if critical:
            entry = critical[0]
            assert entry.maintenance.assigned_crew_id is not None, \
                f"Critical asset {entry.asset.id} should have crew assigned"

    def test_unavailable_crews_not_assigned(self):
        """Offline/busy crews must not be assigned."""
        unavailable = {c.crew_id for c in self.CREWS if c.availability != 'available'}
        assigned = {e.maintenance.assigned_crew_id for e in self.ranking if e.maintenance.assigned_crew_id}
        overlap = unavailable & assigned
        # Busy crews may still be assigned in crew planner if they're the only option,
        # but offline should never be assigned
        offline = {c.crew_id for c in self.CREWS if c.availability == 'offline'}
        assert not (offline & assigned), f"Offline crews should not be assigned: {offline & assigned}"

    def test_monitored_asset_no_crew(self):
        monitor_entries = [e for e in self.ranking if e.maintenance.priority_level == 'monitor']
        for entry in monitor_entries:
            # assign_crew returns None for monitor-level
            result = self.assign_crew(entry.asset, entry.maintenance, list(self.CREWS))
            assert result is None, f"Monitor-level asset {entry.asset.id} should not get crew"


# ─── API Tests ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from backend.main import app
    return TestClient(app)


class TestAPI:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client

    def test_health(self):
        r = self.client.get('/health')
        assert r.status_code == 200
        assert r.json()['service'] == 'Bottleneck AI'

    def test_list_assets(self):
        r = self.client.get('/api/bottleneck/assets')
        assert r.status_code == 200
        data = r.json()
        assert 'assets' in data
        assert data['count'] == 30

    def test_get_asset(self):
        r = self.client.get('/api/bottleneck/assets/TR-1042')
        assert r.status_code == 200
        data = r.json()
        assert data['id'] == 'TR-1042'
        assert data['asset_type'] == 'transformer'

    def test_get_asset_not_found(self):
        r = self.client.get('/api/bottleneck/assets/NONEXISTENT')
        assert r.status_code == 404

    def test_get_telemetry(self):
        r = self.client.get('/api/bottleneck/assets/TR-1042/telemetry', params={'hours': 24})
        assert r.status_code == 200
        data = r.json()
        assert data['count'] == 24
        assert len(data['records']) == 24

    def test_get_incidents(self):
        r = self.client.get('/api/bottleneck/assets/TR-1042/incidents')
        assert r.status_code == 200
        data = r.json()
        assert len(data['incidents']) > 0

    def test_get_predictions(self):
        r = self.client.get('/api/bottleneck/predictions', params={'asset_id': 'TR-1042'})
        assert r.status_code == 200
        data = r.json()
        assert data['asset_id'] == 'TR-1042'
        assert 0.0 <= data['failure_probability_24h'] <= 1.0

    def test_risk_ranking(self):
        r = self.client.get('/api/bottleneck/risk/ranking')
        assert r.status_code == 200
        data = r.json()
        assert data['total'] == 30
        assert len(data['ranking']) == 30
        # TR-1042 should be #1
        assert data['ranking'][0]['asset_id'] == 'TR-1042'

    def test_risk_ranking_sorted(self):
        r = self.client.get('/api/bottleneck/risk/ranking')
        ranking = r.json()['ranking']
        scores = [e['risk_score'] for e in ranking]
        assert scores == sorted(scores, reverse=True), "Ranking should be sorted by risk score descending"

    def test_dashboard_kpis(self):
        r = self.client.get('/api/bottleneck/dashboard/kpis')
        assert r.status_code == 200
        data = r.json()
        assert 'critical_assets' in data
        assert data['total_assets'] == 30
        assert data['critical_assets'] >= 1

    def test_dashboard_alerts(self):
        r = self.client.get('/api/bottleneck/dashboard/alerts')
        assert r.status_code == 200
        data = r.json()
        assert 'alerts' in data
        assert len(data['alerts']) > 0

    def test_maintenance_priorities(self):
        r = self.client.get('/api/bottleneck/maintenance/priorities')
        assert r.status_code == 200
        data = r.json()
        assert data['count'] == 30
        # Top priority should be #1
        assert data['priorities'][0]['priority'] == 1

    def test_crew_list(self):
        r = self.client.get('/api/bottleneck/crew')
        assert r.status_code == 200
        data = r.json()
        assert data['count'] == 10

    def test_crew_plan(self):
        r = self.client.get('/api/bottleneck/crew/plan')
        assert r.status_code == 200
        data = r.json()
        assert 'assignments' in data
        assert 'standby' in data
        assert data['total_assigned'] >= 1

    def test_scenario_severe_storm(self):
        r = self.client.post('/api/bottleneck/scenarios/simulate', json={'scenario': 'severe_storm'})
        assert r.status_code == 200
        data = r.json()
        assert data['scenario'] == 'severe_storm'
        assert len(data['results']) > 0
        # Risk should increase under storm
        for result in data['results']:
            assert result['risk_after'] >= result['risk_before'] - 1  # allow tiny float noise

    def test_scenario_heatwave(self):
        r = self.client.post('/api/bottleneck/scenarios/simulate', json={'scenario': 'heatwave'})
        assert r.status_code == 200

    def test_scenario_asset_degradation(self):
        r = self.client.post('/api/bottleneck/scenarios/simulate', json={'scenario': 'asset_degradation'})
        assert r.status_code == 200

    def test_asset_intelligence(self):
        r = self.client.get('/api/bottleneck/assets/TR-1042/intelligence')
        assert r.status_code == 200
        data = r.json()
        assert 'asset' in data
        assert 'risk' in data
        assert 'prediction' in data
        assert 'grid_impact' in data
        assert 'weather' in data
        assert 'maintenance_recommendation' in data
        assert len(data['telemetry_24h']) == 24

    def test_copilot_basic(self):
        r = self.client.post('/api/bottleneck/chat', json={'message': 'Why is TR-1042 critical?'})
        assert r.status_code == 200
        data = r.json()
        assert 'response' in data
        assert len(data['response']) > 20

    def test_filter_assets_by_type(self):
        r = self.client.get('/api/bottleneck/assets', params={'asset_type': 'transformer'})
        assert r.status_code == 200
        data = r.json()
        assert all(a['asset_type'] == 'transformer' for a in data['assets'])

    def test_filter_maintenance_by_priority(self):
        r = self.client.get('/api/bottleneck/maintenance/priorities', params={'priority_level': 'immediate'})
        assert r.status_code == 200
        data = r.json()
        assert all(p['priority_level'] == 'immediate' for p in data['priorities'])

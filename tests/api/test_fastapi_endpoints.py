"""
FastAPI Endpoint Tests
Comprehensive tests for all v1 API endpoints
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent.absolute())
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from astro_api.v1.deps import get_api_key

from fastapi_app import app
from backend.schemas import ChartResponse, ChartMetadata, PlanetPosition


@pytest.fixture
def client():
    """FastAPI test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_chart_response():
    """Factory for mock ChartResponse"""
    return ChartResponse(
        metadata=ChartMetadata(
            name="Test User",
            datetime="1990-01-15 14:30",
            location="New Delhi, India",
            latitude=28.6,
            longitude=77.2,
            ayanamsa=24.0,
            zodiac_system="Sidereal",
            house_system="Placidus",
            gender="Male"
        ),
        planets={
            "sun": PlanetPosition(
                name="Sun", sign="Capricorn", degree=0.5,
                sign_num=9, abs_pos=270.5
            )
        }
    )


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestChartEndpointValidation:
    """Test input validation for chart generation"""
    
    def test_invalid_date_format(self, client: TestClient):
        """Test rejection of invalid date format"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            "birth_date": "15-01-1990",  # Wrong format DD-MM-YYYY
            "birth_time": "14:30",
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_invalid_time_format(self, client: TestClient):
        """Test rejection of invalid time"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            "birth_date": "1990-01-15",
            "birth_time": "25:00",  # Invalid hour
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_invalid_time_minutes(self, client: TestClient):
        """Test rejection of invalid minutes"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            "birth_date": "1990-01-15",
            "birth_time": "14:70",  # Invalid minutes
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_invalid_gender(self, client: TestClient):
        """Test rejection of invalid gender"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Invalid",  # Must be Male/Female/Other
            "birth_date": "1990-01-15",
            "birth_time": "14:30",
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_empty_name(self, client: TestClient):
        """Test rejection of empty name"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "",
            "gender": "Male",
            "birth_date": "1990-01-15",
            "birth_time": "14:30",
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_missing_required_field(self, client: TestClient):
        """Test rejection when required field missing"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            # birth_date missing
            "birth_time": "14:30",
            "birth_place": "Delhi"
        })
        assert response.status_code == 422
    
    def test_year_out_of_range(self, client: TestClient):
        """Test rejection of year outside valid range"""
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            "birth_date": "1700-01-15",  # Before 1800
            "birth_time": "14:30",
            "birth_place": "Delhi"
        })
        assert response.status_code == 422


class TestChartEndpointSuccess:
    """Test successful chart generation"""
    
    @patch("astro_api.v1.routers.chart.get_location_data")
    @patch("astro_api.v1.routers.chart.generate_vedic_chart")
    def test_generate_chart_success(
        self,
        mock_chart: MagicMock,
        mock_location: MagicMock,
        client: TestClient,
        mock_chart_response: ChartResponse
    ):
        """Test successful chart generation with mocked dependencies"""
        # Mock async location
        mock_location.return_value = (28.6, 77.2, "New Delhi, India")
        
        # Mock chart response
        mock_chart.return_value = mock_chart_response
        
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test User",
            "gender": "Male",
            "birth_date": "1990-01-15",
            "birth_time": "14:30",
            "birth_place": "New Delhi"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "planets" in data
    
    @patch("astro_api.v1.routers.chart.get_location_data")
    def test_location_not_found(
        self,
        mock_location: MagicMock,
        client: TestClient
    ):
        """Test error when location not found"""
        mock_location.return_value = None
        
        response = client.post("/api/v1/chart/generate", json={
            "name": "Test",
            "gender": "Male",
            "birth_date": "1990-01-15",
            "birth_time": "14:30",
            "birth_place": "InvalidLocationXYZ123"
        })
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


class TestAIPredictEndpoint:
    """Test AI prediction endpoint"""
    
    @pytest.fixture(autouse=True)
    def mock_deps(self):
        """Mock dependencies for AI tests"""
        app.dependency_overrides[get_api_key] = lambda: "mock_key"
        yield
        app.dependency_overrides = {}

    def test_missing_chart_data(self, client: TestClient):
        """Test rejection when chart_data missing"""
        response = client.post("/api/v1/ai/predict", json={
            "question": "What is my career outlook?"
            # chart_data missing
        })
        assert response.status_code == 422
    
    def test_empty_question(self, client: TestClient):
        """Test rejection when question is empty"""
        response = client.post("/api/v1/ai/predict", json={
            "chart_data": {"metadata": {}, "planets": {}},
            "question": ""
        })
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling and exception handlers"""
    
    def test_404_for_unknown_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client: TestClient):
        """Test 405 for wrong HTTP method"""
        response = client.get("/api/v1/chart/generate")  # Should be POST
        assert response.status_code == 405


class TestRateLimiting:
    """Test rate limiting behavior"""
    
    def test_health_endpoint_works(self, client: TestClient):
        """Test that health endpoint works repeatedly"""
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

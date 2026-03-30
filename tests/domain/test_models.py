import pytest
from pydantic import ValidationError
from src.domain.models import MasterCity, MasterCityResponse

class TestDomainModels:
    
    def test_master_city_pure_3nf_model(self):
        """
        [TEST 5.1] Valida que el modelo de base de datos puro (MasterCity)
        solo acepta campos de la tabla física y que sus tipos base fallen
        con datos corruptos.
        """
        # Debe construirse exitosamente solo con los campos físicos de la tabla
        valid_city = MasterCity(
            id=1,
            name="Monterrey",
            state_id=10,
            status=1
        )
        assert valid_city.id == 1
        assert valid_city.name == "Monterrey"
        assert valid_city.state_id == 10
        
        # Debe fallar explícitamente si se le inyectan datos erróneos de tipo para id/state_id
        # Ejemplo: Pasar un dict de conexión fallida () o una estructura corrupta
        with pytest.raises(ValidationError):
            MasterCity(name="FailCity", state_id={"invalid": "structure"})
            
    def test_master_city_no_longer_has_join_fields(self):
        """
        [TEST 5.2] Verifica que si intentamos asignarle dinámicamente o por 
        error los campos 'state_name' a la clase base de base de datos, 
        estos no forman parte del esquema estrictamente definido (pueden llegar a existir 
        como arbitrary attributes si pydantic lo permite, pero NO figuran en dump()).
        """
        city = MasterCity(name="Pura", state_id=1)
        # Los campos extra ya no son parte del esquema oficial
        assert "state_name" not in city.model_dump()
        assert "country_name" not in city.model_dump()

    def test_master_city_response_inherits_correctly(self):
        """
        [TEST 5.3] Valida que MasterCityResponse (usada en la API) sí extienda
        correctamente el modelo puro y acepte los campos de JOIN devueltos
        por la base de datos (state_name, country_name).
        """
        response_model = MasterCityResponse(
            id=100,
            name="Guadalajara",
            state_id=5,
            state_name="Jalisco",
            country_name="Mexico"
        )
        assert response_model.id == 100
        assert response_model.state_name == "Jalisco"
        assert response_model.country_name == "Mexico"
        
        # Deben estar incluidos en el modelo retornado a la API
        dumped = response_model.model_dump()
        assert "state_name" in dumped
        assert dumped["state_name"] == "Jalisco"

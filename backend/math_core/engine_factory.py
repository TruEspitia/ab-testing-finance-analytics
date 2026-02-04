# Nuevo archivo: math_core/engine_factory.py
class EngineFactory:
    @staticmethod
    def create_engine(engine_type="auto", context=None):
        if engine_type == "auto":
            # Lógica inteligente de selección
            return SequentialEngine()  # default inteligente
        # resto del factory...

# En main.py (modificado)
@eel.expose
def run_fit(function_name, col_x, col_y, engine="auto"):
    """Ahora soporta engine='auto' además de 'lm', 'de', 'sequential'"""
    optimizer = EngineFactory.create_engine(engine, context={"data_size": len(data)})
    # resto de tu lógica...
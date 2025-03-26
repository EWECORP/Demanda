"""
Nombre del módulo: AA_Nuevo_Class_manager.py

Descripción:   Perfecto. A continuación, se presenta una clase Python denominada ForecastExecutionManager,
pensada para encapsular todas las operaciones CRUD relacionadas con la tabla spl_supply_forecast_execution_execute.

Este patrón permite centralizar la lógica, facilitar pruebas, validar datos y reutilizar la funcionalidad desde múltiples contextos (APIs, scripts, UIs, etc.).

Autor: EWE - Zeetrex
Fecha de creación: [2025-05-23]
"""


from datetime import datetime
import uuid

class ForecastExecutionManager:
    def __init__(self, conn_open_func, conn_close_func, id_generator_func):
        self.Open_Conn_Postgres = conn_open_func
        self.Close_Connection = conn_close_func
        self.id_aleatorio = id_generator_func

        # Columnas actuales de la tabla
        self.columns = [
            "id", "end_execution", "last_execution", "start_execution", "timestamp",
            "supply_forecast_execution_id", "supply_forecast_execution_schedule_id",
            "ext_supplier_code", "graphic", "monthly_net_margin_in_millions",
            "monthly_purchases_in_millions", "monthly_sales_in_millions", "sotck_days",
            "sotck_days_colors", "supplier_id", "supply_forecast_execution_status_id",
            "contains_breaks", "maximum_backorder_days", "otif", "total_products",
            "total_units", "deleted"
        ]

    def create(self, data):
        conn = self.Open_Conn_Postgres()
        if conn is None:
            return None

        try:
            cur = conn.cursor()
            id_exec = self.id_aleatorio()
            timestamp = datetime.utcnow()

            data["id"] = id_exec
            data["timestamp"] = timestamp
            data["deleted"] = False  # Para soft delete

            # Asegurar que estén todos los campos definidos en la tabla
            values = [data.get(col) for col in self.columns]

            insert_query = f"""
                INSERT INTO public.spl_supply_forecast_execution_execute (
                    {', '.join(self.columns)}
                ) VALUES (
                    {', '.join(['%s'] * len(self.columns))}
                )
            """
            cur.execute(insert_query, values)
            conn.commit()
            cur.close()
            return id_exec

        except Exception as e:
            print(f"[ERROR] create(): {e}")
            conn.rollback()
            return None

        finally:
            self.Close_Connection(conn)

    def get(self, exec_id):
        conn = self.Open_Conn_Postgres()
        if conn is None:
            return None

        try:
            cur = conn.cursor()
            query = f"""
                SELECT {', '.join(self.columns)}
                FROM public.spl_supply_forecast_execution_execute
                WHERE id = %s AND deleted = false
            """
            cur.execute(query, (exec_id,))
            row = cur.fetchone()
            cur.close()
            if row:
                return dict(zip(self.columns, row))
            return None

        except Exception as e:
            print(f"[ERROR] get(): {e}")
            return None

        finally:
            self.Close_Connection(conn)

    def update(self, exec_id, updates):
        if not updates:
            print("No hay campos para actualizar.")
            return None

        conn = self.Open_Conn_Postgres()
        if conn is None:
            return None

        try:
            cur = conn.cursor()
            set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
            values = list(updates.values()) + [exec_id]

            query = f"""
                UPDATE public.spl_supply_forecast_execution_execute
                SET {set_clause}
                WHERE id = %s AND deleted = false
            """
            cur.execute(query, values)
            conn.commit()
            cur.close()
            return self.get(exec_id)

        except Exception as e:
            print(f"[ERROR] update(): {e}")
            conn.rollback()
            return None

        finally:
            self.Close_Connection(conn)

    def delete(self, exec_id):
        conn = self.Open_Conn_Postgres()
        if conn is None:
            return False

        try:
            cur = conn.cursor()
            query = """
                UPDATE public.spl_supply_forecast_execution_execute
                SET deleted = true
                WHERE id = %s
            """
            cur.execute(query, (exec_id,))
            conn.commit()
            cur.close()
            return True

        except Exception as e:
            print(f"[ERROR] delete(): {e}")
            conn.rollback()
            return False

        finally:
            self.Close_Connection(conn)

    def hard_delete(self, exec_id):
        conn = self.Open_Conn_Postgres()
        if conn is None:
            return False

        try:
            cur = conn.cursor()
            query = """
                DELETE FROM public.spl_supply_forecast_execution_execute
                WHERE id = %s
            """
            cur.execute(query, (exec_id,))
            conn.commit()
            cur.close()
            return True

        except Exception as e:
            print(f"[ERROR] hard_delete(): {e}")
            conn.rollback()
            return False

        finally:
            self.Close_Connection(conn)


# Solo importa lo necesario desde el módulo de funciones
from funciones_forecast import (
    get_forecast,
    Open_Conn_Postgres,
    Close_Connection,
    id_aleatorio,
    generar_datos,
    Procesar_ALGO_01,
    Procesar_ALGO_02,
    Procesar_ALGO_03,
    Procesar_ALGO_04,
    Procesar_ALGO_05,
    Procesar_ALGO_06,    
    generar_datos,    
    get_execution_execute_by_status,
    get_execution_execute_parameter,
    update_execution
)



# Ejemplo de uso
manager = ForecastExecutionManager(Open_Conn_Postgres, Close_Connection, id_aleatorio)

# Crear un nuevo registro
nuevo_id = manager.create({
    "end_execution": datetime.utcnow(),
    "last_execution": True,
    "start_execution": datetime.utcnow(),
    "supply_forecast_execution_id": "uuid-ejecución",
    "supply_forecast_execution_schedule_id": "uuid-cronograma",
    "ext_supplier_code": "PROV001",
    "graphic": "<svg>...</svg>",
    "monthly_net_margin_in_millions": 4.0,
    "monthly_purchases_in_millions": 40.0,
    "monthly_sales_in_millions": 50.0,
    "sotck_days": 20,
    "sotck_days_colors": "verde",
    "supplier_id": "uuid-proveedor",
    "supply_forecast_execution_status_id": 1,
    "contains_breaks": "N",
    "maximum_backorder_days": 5,
    "otif": 94.5,
    "total_products": 20,
    "total_units": 10500
})

# Leer el registro insertado
print(manager.get(nuevo_id))

# Actualizar campos
manager.update(nuevo_id, {"otif": 97.8, "last_execution": False})

# Soft delete
manager.delete(nuevo_id)


#----------------------------------------------------------------
#PREPARAR PARA API REST
#----------------------------------------------------------------       

import unittest
from datetime import datetime, timedelta
from uuid import uuid4

# Simulaciones básicas para testeo
mock_db = {}

def mock_open_conn():
    return "mock_connection"

def mock_close_conn(conn):
    pass

def mock_id_generator():
    return str(uuid4())

class MockCursor:
    def __init__(self):
        self.last_query = ""
        self.last_values = []

    def execute(self, query, values):
        self.last_query = query
        self.last_values = values
        if "INSERT" in query:
            mock_db[values[0]] = dict(zip(ForecastExecutionManager(mock_open_conn, mock_close_conn, mock_id_generator).columns, values))
        elif "UPDATE" in query and "deleted = true" in query:
            mock_db[values[0]]["deleted"] = True
        elif "UPDATE" in query:
            keys = query.split("SET")[1].split("WHERE")[0].split(",")
            keys = [k.strip().split(" = ")[0] for k in keys]
            for i, k in enumerate(keys):
                mock_db[values[-1]][k] = values[i]
        elif "DELETE" in query:
            del mock_db[values[0]]

    def fetchone(self):
        id_val = self.last_values[0]
        if id_val in mock_db and not mock_db[id_val].get("deleted", False):
            return tuple(mock_db[id_val].get(col) for col in ForecastExecutionManager(mock_open_conn, mock_close_conn, mock_id_generator).columns)
        return None

    def close(self):
        pass

class ForecastExecutionManagerTest(unittest.TestCase):
    def setUp(self):
        ForecastExecutionManager.cursor_class = MockCursor  # Injectamos el mock
        self.manager = ForecastExecutionManager(mock_open_conn, mock_close_conn, mock_id_generator)

    def test_create_and_get(self):
        data = {
            "end_execution": datetime.utcnow(),
            "last_execution": True,
            "start_execution": datetime.utcnow() - timedelta(hours=1),
            "supply_forecast_execution_id": str(uuid4()),
            "supply_forecast_execution_schedule_id": str(uuid4()),
            "ext_supplier_code": "TEST001",
            "graphic": "<svg>graf</svg>",
            "monthly_net_margin_in_millions": 1.5,
            "monthly_purchases_in_millions": 15.0,
            "monthly_sales_in_millions": 18.2,
            "sotck_days": 10.5,
            "sotck_days_colors": "verde",
            "supplier_id": str(uuid4()),
            "supply_forecast_execution_status_id": 1,
            "contains_breaks": "N",
            "maximum_backorder_days": 2,
            "otif": 96.2,
            "total_products": 10,
            "total_units": 2400.0
        }

        new_id = self.manager.create(data)
        self.assertIsNotNone(new_id)

        result = self.manager.get(new_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["ext_supplier_code"], "TEST001")

    def test_update(self):
        # Crear uno nuevo primero
        data = {
            "end_execution": datetime.utcnow(),
            "last_execution": True,
            "start_execution": datetime.utcnow(),
            "supply_forecast_execution_id": str(uuid4()),
            "supply_forecast_execution_schedule_id": str(uuid4()),
            "ext_supplier_code": "PROVXYZ",
            "graphic": "<svg></svg>",
            "monthly_net_margin_in_millions": 2.0,
            "monthly_purchases_in_millions": 25.0,
            "monthly_sales_in_millions": 27.0,
            "sotck_days": 5,
            "sotck_days_colors": "rojo",
            "supplier_id": str(uuid4()),
            "supply_forecast_execution_status_id": 2,
            "contains_breaks": "S",
            "maximum_backorder_days": 3,
            "otif": 89.0,
            "total_products": 30,
            "total_units": 7500.0
        }
        exec_id = self.manager.create(data)
        updated = self.manager.update(exec_id, {"otif": 92.3, "last_execution": False})
        self.assertIsNotNone(updated)
        self.assertEqual(updated["otif"], 92.3)
        self.assertFalse(updated["last_execution"])

    def test_soft_delete(self):
        data = {
            "end_execution": datetime.utcnow(),
            "last_execution": True,
            "start_execution": datetime.utcnow(),
            "supply_forecast_execution_id": str(uuid4()),
            "supply_forecast_execution_schedule_id": str(uuid4()),
            "ext_supplier_code": "TO_DELETE",
            "graphic": "<svg></svg>",
            "monthly_net_margin_in_millions": 0,
            "monthly_purchases_in_millions": 0,
            "monthly_sales_in_millions": 0,
            "sotck_days": 0,
            "sotck_days_colors": "",
            "supplier_id": str(uuid4()),
            "supply_forecast_execution_status_id": 1,
            "contains_breaks": "N",
            "maximum_backorder_days": 0,
            "otif": 0,
            "total_products": 0,
            "total_units": 0
        }
        exec_id = self.manager.create(data)
        self.assertTrue(self.manager.delete(exec_id))
        self.assertIsNone(self.manager.get(exec_id))

if __name__ == '__main__':
    unittest.main()

# QuantConnect API - Guía para Frontend

## 🚀 **Endpoints Disponibles**

### **Base URL:** `/api/quantconnect/`

---

## 📋 **1. Flujo Completo (Recomendado)**

### **POST** `/api/quantconnect/complete-flow/`

Ejecuta todo el flujo: crear proyecto → archivo → compilar → ejecutar backtest → obtener resultados

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body:**
```json
{
    "strategy_name": "Mi Estrategia",
    "python_code": "from AlgorithmImports import *\n\nclass MyStrategy(QCAlgorithm):\n    def Initialize(self):\n        self.SetStartDate(2024, 1, 1)\n        self.SetEndDate(2024, 2, 1)\n        self.SetCash(10000)\n        self.AddEquity(\"SPY\", Resolution.DAILY)\n        \n    def OnData(self, data):\n        if not self.Portfolio.Invested:\n            self.SetHoldings(\"SPY\", 1)",
    "backtest_name": "Mi Backtest"
}
```

**Respuesta Exitosa:**
```json
{
    "success": true,
    "message": "Backtest completed successfully",
    "results": {
        "project_id": 24938555,
        "compile_id": "ab1403d6da234b2200b576ead18ec330",
        "backtest_id": "79cb1ecc0ac22070854fef182e956212",
        "steps": [
            {
                "step": "create_project",
                "success": true,
                "project_id": 24938555
            },
            {
                "step": "create_file",
                "success": true
            },
            {
                "step": "compile_project",
                "success": true,
                "compile_id": "ab1403d6da234b2200b576ead18ec330"
            },
            {
                "step": "compilation_completed",
                "success": true,
                "state": "BuildSuccess"
            },
            {
                "step": "backtest_started",
                "success": true,
                "backtest_id": "79cb1ecc0ac22070854fef182e956212",
                "status": "In Queue..."
            },
            {
                "step": "backtest_completed",
                "success": true,
                "status": "Completed.",
                "progress": 100
            }
        ],
        "final_results": {
            "statistics": {
                "Total Orders": "3",
                "Compounding Annual Return": "10.211%",
                "Drawdown": "18.200%",
                "Sharpe Ratio": "0.193",
                "Start Equity": "100000",
                "End Equity": "113023.67",
                "Net Profit": "13.024%"
            }
        }
    }
}
```

---

## 🔧 **2. Endpoints Individuales**

### **POST** `/api/quantconnect/direct/`

Endpoint multipropósito para operaciones individuales.

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Crear Proyecto:**
```json
{
    "action": "create_project",
    "name": "Mi Proyecto",
    "language": "Py"
}
```

#### **Crear Archivo:**
```json
{
    "action": "create_file",
    "project_id": 24938555,
    "filename": "main.py",
    "content": "código python aquí"
}
```

#### **Compilar Proyecto:**
```json
{
    "action": "compile_project",
    "project_id": 24938555
}
```

#### **Verificar Compilación:**
```json
{
    "action": "check_compilation",
    "project_id": 24938555,
    "compile_id": "ab1403d6da234b2200b576ead18ec330"
}
```

#### **Ejecutar Backtest:**
```json
{
    "action": "run_backtest",
    "project_id": 24938555,
    "compile_id": "ab1403d6da234b2200b576ead18ec330",
    "backtest_name": "Mi Backtest"
}
```

#### **Verificar Estado del Backtest:**
```json
{
    "action": "check_backtest_status",
    "project_id": 24938555,
    "backtest_id": "79cb1ecc0ac22070854fef182e956212"
}
```

#### **Obtener Resultados:**
```json
{
    "action": "get_backtest_results",
    "project_id": 24938555,
    "backtest_id": "79cb1ecc0ac22070854fef182e956212"
}
```

---

## 📊 **3. Monitoreo en Tiempo Real**

### **GET** `/api/quantconnect/monitor/`

**Parámetros de Query:**
- `type`: `"compilation"` o `"backtest"`
- `project_id`: ID del proyecto
- `compile_id`: ID de compilación (si type=compilation)
- `backtest_id`: ID del backtest (si type=backtest)

**Ejemplos:**

#### **Monitorear Compilación:**
```
GET /api/quantconnect/monitor/?type=compilation&project_id=24938555&compile_id=ab1403d6da234b2200b576ead18ec330
```

#### **Monitorear Backtest:**
```
GET /api/quantconnect/monitor/?type=backtest&project_id=24938555&backtest_id=79cb1ecc0ac22070854fef182e956212
```

**Respuesta:**
```json
{
    "success": true,
    "state": "BuildSuccess",  // o "InQueue", "BuildError", etc.
    "completed": true,
    "failed": false,
    "logs": ["Build Request Successful..."]
}
```

---

## 🎯 **4. Implementación en Frontend**

### **Ejemplo con JavaScript/React:**

```javascript
// Función para ejecutar backtest completo
async function runQuantConnectBacktest(pythonCode, strategyName) {
    try {
        const response = await fetch('/api/quantconnect/complete-flow/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_name: strategyName,
                python_code: pythonCode,
                backtest_name: `${strategyName} Backtest`
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Backtest completado:', data.results);
            return data.results;
        } else {
            console.error('Error:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Error de red:', error);
        return null;
    }
}

// Función para monitorear en tiempo real
async function monitorQuantConnect(type, projectId, id) {
    const params = new URLSearchParams({
        type: type,
        project_id: projectId,
        [type === 'compilation' ? 'compile_id' : 'backtest_id']: id
    });
    
    try {
        const response = await fetch(`/api/quantconnect/monitor/?${params}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error de monitoreo:', error);
        return null;
    }
}

// Ejemplo de uso
const pythonCode = `
from AlgorithmImports import *

class MyStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2024, 2, 1)
        self.SetCash(10000)
        self.AddEquity("SPY", Resolution.DAILY)
        
    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings("SPY", 1)
`;

runQuantConnectBacktest(pythonCode, "Mi Estrategia SPY");
```

---

## 📈 **5. Estados y Progreso**

### **Estados de Compilación:**
- `InQueue`: En cola
- `BuildInProgress`: Compilando
- `BuildSuccess`: Compilación exitosa
- `BuildError`: Error de compilación

### **Estados de Backtest:**
- `In Queue...`: En cola
- `Running`: Ejecutándose
- `Completed.`: Completado
- `Failed`: Falló
- `Error`: Error

### **Progreso:**
- `0-100`: Porcentaje de progreso
- `100`: Completado

---

## ⚠️ **6. Manejo de Errores**

### **Errores Comunes:**
- `400 Bad Request`: Parámetros faltantes o inválidos
- `401 Unauthorized`: Token JWT inválido o expirado
- `500 Internal Server Error`: Error del servidor

### **Respuesta de Error:**
```json
{
    "success": false,
    "error": "Descripción del error"
}
```

---

## 🚀 **7. Ejemplo de Flujo Completo en Frontend**

```javascript
class QuantConnectManager {
    constructor() {
        this.baseURL = '/api/quantconnect';
        this.token = localStorage.getItem('token');
    }
    
    async runCompleteBacktest(strategy) {
        // 1. Ejecutar flujo completo
        const result = await this.executeCompleteFlow(strategy);
        
        if (result && result.success) {
            // 2. Mostrar resultados
            this.displayResults(result.results.final_results);
            return result.results;
        }
        
        return null;
    }
    
    async executeCompleteFlow(strategy) {
        const response = await fetch(`${this.baseURL}/complete-flow/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_name: strategy.name,
                python_code: strategy.code,
                backtest_name: `${strategy.name} Backtest`
            })
        });
        
        return await response.json();
    }
    
    displayResults(results) {
        const stats = results.statistics;
        console.log(`Retorno Total: ${stats['Net Profit']}`);
        console.log(`Sharpe Ratio: ${stats['Sharpe Ratio']}`);
        console.log(`Drawdown: ${stats['Drawdown']}`);
    }
}

// Uso
const qcManager = new QuantConnectManager();
qcManager.runCompleteBacktest({
    name: "Estrategia SPY",
    code: "código python aquí"
});
```

---

## ✅ **¡Listo para Usar!**

La API está completamente funcional y lista para integrar con el frontend. Todos los endpoints están probados y funcionando correctamente con la API real de QuantConnect.

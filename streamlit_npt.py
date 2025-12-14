import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="Calculadora NPT | UCI",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CORE LOGIC (Ported from logic.js) ---
class NPT:
    @staticmethod
    def round_val(v, d=0):
        if d == 0:
            return int(round(v))
        return round(v, d)

    @staticmethod
    def calc_bmi(weight, height_cm):
        if height_cm > 0:
            return weight / ((height_cm / 100) ** 2)
        return 0.0

    @staticmethod
    def calc_ibw(sex, height_cm):
        # Devine Formula
        base = 50 if sex == 'H' else 45.5
        return base + 0.9 * (height_cm - 152)

    @staticmethod
    def calc_adj_bw(ibw, actual_weight):
        return ibw + 0.25 * (actual_weight - ibw)

    @staticmethod
    def get_calc_weight(actual, adj, bmi):
        return adj if bmi >= 30 else actual

    @staticmethod
    def calculate(params):
        weight_calc = params['weight_calc']
        kcal_kg = params['kcal_kg']
        prot_kg = params['prot_kg']
        start_pct = params['start_pct']
        pct_gluc = params['pct_gluc']
        aa_pct = params['aa_pct']

        # Energy
        kcal_target = kcal_kg * weight_calc
        kcal_day = kcal_target * start_pct

        # Protein
        prot_day = prot_kg * weight_calc
        nitrogen_day = prot_day / 6.25
        kcal_prot = prot_day * 4

        # Non-Protein Calories
        kcal_no_prot = max(kcal_day - kcal_prot, 0)
        kcal_gluc = kcal_no_prot * (pct_gluc / 100.0)
        kcal_lip = kcal_no_prot - kcal_gluc

        # Grams
        g_gluc = kcal_gluc / 3.4
        g_lip = kcal_lip / 9.0

        # Volumes
        ml_d50 = g_gluc / 0.5
        ml_lip20 = g_lip / 0.2
        ml_aa = (prot_day * 100) / aa_pct

        vol_total = ml_aa + ml_d50 + ml_lip20
        rate = vol_total / 24.0

        return {
            "kcal_target": kcal_target,
            "kcal_day": kcal_day,
            "prot_day": prot_day,
            "nitrogen_day": nitrogen_day,
            "g_gluc": g_gluc,
            "g_lip": g_lip,
            "ml_d50": ml_d50,
            "ml_lip20": ml_lip20,
            "ml_aa": ml_aa,
            "vol_total": vol_total,
            "rate": rate
        }

    @staticmethod
    def check_safety(res, weight_calc):
        g_gluc = res['g_gluc']
        g_lip = res['g_lip']

        # Glucose Infusion Rate
        gir_g_kg_d = g_gluc / weight_calc if weight_calc > 0 else 0
        gir_mg_kg_min = (g_gluc * 1000) / (weight_calc * 1440) if weight_calc > 0 else 0
        
        gluc_ok = gir_g_kg_d <= 5
        gluc_msg = "Excede 5 g/kg/d. Riesgo de hiperglucemia/↑CO₂." if not gluc_ok else "Dentro de rangos seguros."

        # Lipid Load
        lip_g_kg_d = g_lip / weight_calc if weight_calc > 0 else 0
        lip_ok = lip_g_kg_d <= 1.5
        lip_warn = lip_g_kg_d < 0.7
        
        if not lip_ok:
            lip_msg = "Excede 1.5 g/kg/d (Sobrecarga)."
        elif lip_warn:
            lip_msg = "Bajo aporte (<0.7 g/kg/d). Riesgo déficit AGE."
        else:
            lip_msg = "Aporte correcto."

        return {
            "glucose": {"val": gir_g_kg_d, "ok": gluc_ok, "msg": gluc_msg},
            "lipids": {"val": lip_g_kg_d, "ok": lip_ok, "warn": lip_warn, "msg": lip_msg}
        }

# --- UI ---
def main():
    st.title("Calculadora NPT | UCI 🏥")
    st.markdown("Nutrición Parenteral en Paciente Crítico")

    # Sidebar inputs
    with st.sidebar:
        st.header("1. Datos del Paciente")
        col1, col2 = st.columns(2)
        with col1:
            edad = st.number_input("Edad", 14, 120, 65)
            sexo = st.selectbox("Sexo", ["H", "M"])
        with col2:
            peso = st.number_input("Peso (kg)", 20.0, 300.0, 70.0, step=0.1)
            talla = st.number_input("Talla (cm)", 100, 250, 175)

        estres_opt = st.selectbox("Nivel de Estrés", ["Bajo / Estándar", "Alto (Sepsis/Trauma)"])
        estres = "si" if "Alto" in estres_opt else "no"
        
        refeeding_opt = st.selectbox("Riesgo Realimentación", ["No", "Sí (Desnutrición)"])
        refeeding = "si" in refeeding_opt
        
        col3, col4 = st.columns(2)
        with col3:
            epoc_opt = st.selectbox("EPOC", ["No", "Sí"])
            epoc = "Sí" in epoc_opt
        with col4:
            fistula_opt = st.selectbox("Fístulas", ["No", "Sí"])
            fistula = "Sí" in fistula_opt

        st.header("2. Objetivos")
        
        # Suggestion badge logic
        sug_kcal, sug_prot = 25, 1.5
        if estres == "si":
            sug_kcal, sug_prot = 30, 1.5
            st.info(f"💡 Sugerido (Estrés): {sug_kcal} kcal/kg, {sug_prot} g prot")

        kcal_kg = st.number_input("Calorías Objetivo (kcal/kg/d)", 10, 50, 25)
        
        # Start Phase Slider
        start_pct_int = st.slider("Fase de Inicio (% de meta)", 25, 100, 80, 5, format="%d%%")
        start_pct = start_pct_int / 100.0
        st.caption(f"Día actual: {start_pct_int}% de la meta")

        prot_kg = st.number_input("Proteínas (g/kg/d)", 0.5, 3.0, 1.5, step=0.1)

        st.subheader("Distribución No Proteica")
        pct_gluc = st.slider("Glucosa (%)", 30, 90, 65, 5)
        st.caption(f"Glucosa: {pct_gluc}% | Lípidos: {100-pct_gluc}%")

        aa_pct = st.number_input("Conc. Aminoácidos (%)", 5, 25, 15)


    # Calculation
    bmi = NPT.calc_bmi(peso, talla)
    ibw = NPT.calc_ibw(sexo, talla)
    adj_bw = NPT.calc_adj_bw(ibw, peso)
    weight_calc = NPT.get_calc_weight(peso, adj_bw, bmi)
    is_obese = bmi >= 30

    params = {
        "weight_calc": weight_calc,
        "kcal_kg": kcal_kg,
        "prot_kg": prot_kg,
        "start_pct": start_pct,
        "pct_gluc": pct_gluc,
        "aa_pct": aa_pct
    }
    
    res = NPT.calculate(params)
    safety = NPT.check_safety(res, weight_calc)

    # Main Area
    
    # 1. Top Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IMC", f"{bmi:.1f}", "Obesidad" if is_obese else None, delta_color="inverse")
    c2.metric("Peso Cálculo", f"{weight_calc:.1f} kg", "Usado para dosis")
    c3.metric("Kcal Totales (Hoy)", f"{int(res['kcal_day'])}", f"{int(start_pct*100)}% Meta")
    c4.metric("Volumen Total", f"{int(res['vol_total'])} ml", f"{int(res['rate'])} ml/h")

    # 2. Composition (styled cards)
    st.subheader("Composición de la Bolsa")
    
    col_prot, col_gluc, col_lip = st.columns(3)
    
    with col_prot:
        st.markdown(f"""
        <div style="background-color:rgba(33, 150, 243, 0.1); padding:15px; border-radius:10px; border:1px solid #2196F3;">
            <h3 style="margin:0; color:#2196F3;">Proteínas</h3>
            <p style="font-size:2em; font-weight:bold; margin:0;">{int(res['prot_day'])} g</p>
            <p style="margin:0; opacity:0.8;">{int(res['ml_aa'])} ml (AA {aa_pct}%)</p>
            <small>Nitrógeno: {res['nitrogen_day']:.1f} g</small>
        </div>
        """, unsafe_allow_html=True)

    with col_gluc:
        color = "#4CAF50" if safety['glucose']['ok'] else "#F44336"
        st.markdown(f"""
        <div style="background-color:rgba(76, 175, 80, 0.1); padding:15px; border-radius:10px; border:1px solid {color};">
            <h3 style="margin:0; color:{color};">Glucosa</h3>
            <p style="font-size:2em; font-weight:bold; margin:0;">{int(res['g_gluc'])} g</p>
            <p style="margin:0; opacity:0.8;">{int(res['ml_d50'])} ml (D50%)</p>
            <small>{safety['glucose']['val']:.2f} g/kg/d</small>
        </div>
        """, unsafe_allow_html=True)

    with col_lip:
        color = "#4CAF50" if safety['lipids']['ok'] and not safety['lipids']['warn'] else ("#FF9800" if safety['lipids']['warn'] else "#F44336")
        st.markdown(f"""
        <div style="background-color:rgba(255, 152, 0, 0.1); padding:15px; border-radius:10px; border:1px solid {color};">
            <h3 style="margin:0; color:{color};">Lípidos</h3>
            <p style="font-size:2em; font-weight:bold; margin:0;">{int(res['g_lip'])} g</p>
            <p style="margin:0; opacity:0.8;">{int(res['ml_lip20'])} ml (Lip 20%)</p>
            <small>{safety['lipids']['val']:.2f} g/kg/d</small>
        </div>
        """, unsafe_allow_html=True)

    # Safety Alerts
    st.write("---")
    st.subheader("Seguridad y Alertas")
    
    if not safety['glucose']['ok']:
        st.error(f"⚠️ GLUCOSA: {safety['glucose']['msg']}")
    
    if not safety['lipids']['ok']:
        st.error(f"⚠️ LÍPIDOS: {safety['lipids']['msg']}")
    elif safety['lipids']['warn']:
        st.warning(f"⚠️ LÍPIDOS: {safety['lipids']['msg']}")

    if refeeding:
        st.warning("⚠️ RIESGO REALIMENTACIÓN: Iniciar a 25-50%. Añadir Tiamina IV 100-200mg.")
    if epoc:
        st.warning("⚠️ EPOC: Monitorizar producción de CO₂. Evitar sobrecarga de glucosa.")
    if fistula:
        st.info("ℹ️ FÍSTULAS: Considerar Zinc extra (10-20 mg/d).")
    
    if safety['glucose']['ok'] and safety['lipids']['ok'] and not refeeding and not epoc:
        st.success("✅ Parámetros dentro de rangos estándar.")

    # 3. Guide & Prescription
    st.write("---")
    t1, t2 = st.tabs(["Guía Didáctica", "Orden Médica (Copiar)"])
    
    with t1:
        st.markdown(f"""
        #### 4) Pasos para prescribir NP
        1. **Valorar vía**: Priorizar NE si es posible (<60% tras 5-7 días).
        2. **Peso de cálculo**: {'PA (Obesidad)' if is_obese else 'Peso Real'}.
        3. **Fija energía**: {kcal_kg} kcal/kg x {weight_calc:.1f} kg = **{int(res['kcal_target'])} kcal**. (Inicio {int(start_pct*100)}% = {int(res['kcal_day'])} kcal).
        4. **Proteínas**: {prot_kg} g/kg → **{int(res['prot_day'])} g**.
        5. **No proteicas**: Glucosa {pct_gluc}% (**{int(res['g_gluc'])} g**) y Lípidos {100-pct_gluc}% (**{int(res['g_lip'])} g**).
        6. **Electrolitos**: Na/K 1-2 mEq/kg; P 20-40 mmol; Mg 8-20 mEq. + Vitaminas/Oligoelementos.
        7. **Volumen**: **{int(res['vol_total'])} ml** a **{int(res['rate'])} ml/h**.
        8. **Monitorizar**: Glucemia 140-180, TG < 400.
        """)

        st.subheader("Notas de seguridad, trucos y errores")
        
        with st.expander("Precauciones clave", expanded=True):
            st.warning("""
            *   **Máximo glucosa:** ≤ 5 g/kg/día (≈ ≤ 5 mg/kg/min). Mantén menor aporte si hiperglucemia o EPOC.
            *   **Lípidos:** 0,7–1,0 g/kg/día (máx. 1,5). Triglicéridos: si >400 mg/dL → reduce/pausa lípidos.
            *   **EPOC / hipercapnia:** favorece distribución con menor carga de glucosa (p.ej., 50–60% de no proteicas) y evita superar los límites de infusión de glucosa para no aumentar la producción de CO₂.
            *   **Zinc extra:** 10–20 mg/d si fístulas, grandes pérdidas, diarrea o quemaduras.
            *   **Riesgo de realimentación / desnutrición:** iniciar al 25–50% + tiamina 100–200 mg IV/d y monitorizar estrechamente P–K–Mg.
            """)

        with st.expander("Trucos y errores frecuentes"):
            st.info("""
            *   **Error:** dar 100% de kcal desde el día 1 → *Mejor*: 70–80% y subir.
            *   **Error:** olvidar vitaminas/oligoelementos → *Siempre* añadirlos.
            *   **Error:** exceder glucosa (>5 g/kg/d) → hiperglucemia/↑CO₂.
            *   **Error:** no vigilar **P** al inicio → riesgo de **realimentación**.
            *   **Error:** ignorar **TG** → si >400 mg/dL, reduce lípidos.
            *   **Error:** no considerar **peso ajustado** en obesidad → sobreestimación.
            *   **Tip:** prioriza **proteína plena** aunque kcal sean hipocalóricas los primeros días.
            *   **Tip:** documenta **Balance N** 1–2/sem para seguir el catabolismo.
            """)
        
    with t2:
        weight_lbl = f"PA {weight_calc:.1f}" if is_obese else f"{weight_calc:.1f}"
        
        prescription_text = f"""ORDEN DE NUTRICIÓN PARENTERAL
----------------------------------------
PACIENTE:
Peso Cálculo: {weight_lbl} kg (IMC {bmi:.1f})
Situación: {'Sepsis/Estrés' if estres=='si' else 'Estándar'} | {'Riesgo Realimentación' if refeeding else 'Sin Riesgo Realimentación'}

APORTE DIARIO (Día {int(start_pct*100)}% de la meta):
• Calorías Totales: {int(res['kcal_day'])} kcal
• Proteínas:        {int(res['prot_day'])} g  (Nitrógeno {res['nitrogen_day']:.1f} g)
• Glucosa:          {int(res['g_gluc'])} g  ({pct_gluc}% no prot)
• Lípidos:          {int(res['g_lip'])} g  ({100-pct_gluc}% no prot)

COMPOSICIÓN DE LA BOLSA:
1. Aminoácidos ({aa_pct}%):     {int(res['ml_aa'])} mL
2. Dextrosa 50%:          {int(res['ml_d50'])} mL
3. Lípidos 20%:           {int(res['ml_lip20'])} mL

VOLUMEN Y RITMO:
• Volumen Total:    {int(res['vol_total'])} mL (más aditivos)
• Ritmo de Infusión: {int(res['rate'])} mL/h (en 24h)

ADITIVOS SUGERIDOS:
• Na/K: 1-2 mEq/kg/d
• P (Fosfato): 20-40 mmol/d
• Mg: 8-20 mEq/d | Ca: 10-15 mEq/d
• Multivitamínico + Oligoelementos: 1 vial/día
{ '• ZINC EXTRA: 10-20 mg/d' if fistula else '' }
{ '• TIAMINA: 100-200 mg IV' if refeeding else '' }

MONITORIZACIÓN:
• Glucemia 140-180 mg/dL.
• Triglicéridos a las 48-72h.
"""
        st.text_area("Copia este texto:", value=prescription_text, height=400)
        st.caption("Usa el botón de copiar que aparece al pasar el ratón por encima del bloque de código si está disponible, o selecciona todo y copia manual.")

if __name__ == "__main__":
    main()

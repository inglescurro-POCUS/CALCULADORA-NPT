/**
 * Application Controller
 * Handles UI interactions and updates.
 */

const App = {
    init: () => {
        App.bindEvents();
        App.updateTheme(); // Init theme
        App.calculate();   // Initial calc
    },

    bindEvents: () => {
        // Theme Toggles
        document.getElementById('theme-toggle').addEventListener('click', App.toggleTheme);

        // Input Changes - Realtime calculation
        const inputs = document.querySelectorAll('input, select');
        inputs.forEach(el => {
            el.addEventListener('input', (e) => {
                // Handle specific UI updates (ranges)
                if (e.target.id === 'arranque') {
                    document.getElementById('arranqueVal').textContent = Math.round(e.target.value * 100);
                }
                if (e.target.id === 'pctGluc') {
                    const val = e.target.value;
                    document.getElementById('pctGlucVal').textContent = val;
                    document.getElementById('pctLipVal').textContent = 100 - val;
                }
                if (e.target.id === 'estres') {
                    App.suggestValues();
                }

                App.calculate();
            });
        });

        // Copy Button
        document.getElementById('btn-copy').addEventListener('click', App.copyPrescription);
    },

    toggleTheme: () => {
        const body = document.body;
        const current = body.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        body.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    },

    updateTheme: () => {
        const saved = localStorage.getItem('theme') || 'dark';
        document.body.setAttribute('data-theme', saved);
    },

    suggestValues: () => {
        const estres = document.getElementById('estres').value;
        const kcalInput = document.getElementById('kcalKg');
        const protInput = document.getElementById('protKg');
        const badge = document.getElementById('suggestion-badge');

        if (estres === 'si') {
            if (parseFloat(kcalInput.value) < 26) kcalInput.value = 30;
            if (parseFloat(protInput.value) < 1.4) protInput.value = 1.5;
            badge.textContent = 'Sugerido: 30 kcal/kg, 1.5g prot';
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    },

    getValues: () => {
        return {
            age: parseFloat(document.getElementById('edad').value) || 65,
            sex: document.getElementById('sexo').value,
            weight: parseFloat(document.getElementById('peso').value) || 70,
            height: parseFloat(document.getElementById('talla').value) || 175,
            stress: document.getElementById('estres').value,
            refeeding: document.getElementById('refeeding').value === 'si',
            epoc: document.getElementById('epoc').value === 'si',
            fistula: document.getElementById('fistulas').value === 'si',
            kcalKg: parseFloat(document.getElementById('kcalKg').value) || 25,
            startPct: parseFloat(document.getElementById('arranque').value) || 0.8,
            protKg: parseFloat(document.getElementById('protKg').value) || 1.5,
            pctGluc: parseFloat(document.getElementById('pctGluc').value) || 65,
            aaPct: parseFloat(document.getElementById('aaPct').value) || 15
        };
    },

    calculate: () => {
        const v = App.getValues();

        // 1. Anthropometry
        const bmi = NPT.calcBMI(v.weight, v.height);
        const ibw = NPT.calcIBW(v.sex, v.height);
        const adjBW = NPT.calcAdjBW(ibw, v.weight);
        const weightCalc = NPT.getCalculationWeight(v.weight, adjBW, bmi);
        const isObese = bmi >= 30;

        // UI Updates: Body
        document.getElementById('res-imc').textContent = NPT.round(bmi, 1);
        document.getElementById('res-weight-calc').textContent = NPT.round(weightCalc, 1) + ' kg';
        document.getElementById('badge-obesity').style.display = isObese ? 'inline-block' : 'none';

        // 2. Requirements
        const res = NPT.calculateRequirements({
            weightCalc,
            kcalKg: v.kcalKg,
            protKg: v.protKg,
            startPct: v.startPct,
            pctGluc: v.pctGluc,
            aaPct: v.aaPct
        });

        // UI Updates: Main Results
        document.getElementById('res-kcal-total').textContent = NPT.round(res.kcalDay, 0);
        document.getElementById('res-prot-g').textContent = NPT.round(res.protDay, 0);
        document.getElementById('res-nit-g').textContent = NPT.round(res.nitrogenDay, 1);
        document.getElementById('res-vol-total').textContent = NPT.round(res.volTotal, 0);
        document.getElementById('res-rate').textContent = NPT.round(res.rate, 0);

        // Composition Details
        document.getElementById('val-gluc-g').textContent = NPT.round(res.gGlu, 0);
        document.getElementById('val-gluc-ml').textContent = NPT.round(res.mlD50, 0);

        document.getElementById('val-lip-g').textContent = NPT.round(res.gLip, 0);
        document.getElementById('val-lip-ml').textContent = NPT.round(res.mlLip20, 0);

        document.getElementById('val-aa-ml').textContent = NPT.round(res.mlAA, 0);

        // 3. Safety & Warnings
        const safety = NPT.checkSafety(res, weightCalc);

        const alertGluc = document.getElementById('alert-gluc');
        alertGluc.className = `alert ${safety.glucose.ok ? 'alert-success' : 'alert-danger'}`;
        alertGluc.textContent = `Glucosa: ${NPT.round(safety.glucose.val, 2)} g/kg/d. ${safety.glucose.msg}`;

        const alertLip = document.getElementById('alert-lip');
        let lipClass = 'alert-success';
        if (!safety.lipids.ok) lipClass = 'alert-danger';
        else if (safety.lipids.warn) lipClass = 'alert-warning';
        alertLip.className = `alert ${lipClass}`;
        alertLip.textContent = `Lípidos: ${NPT.round(safety.lipids.val, 2)} g/kg/d. ${safety.lipids.msg}`;

        // Context Warnings
        const alertCtx = document.getElementById('alert-ctx');
        let ctxMsgs = [];
        if (v.refeeding) ctxMsgs.push("⚠️ Riesgo Realimentación: Iniciar al 25-50% (actual " + Math.round(v.startPct * 100) + "%). Añadir Tiamina IV.");
        if (v.epoc) ctxMsgs.push("⚠️ EPOC: Evitar sobrecarga de glucosa (mantener <50-60% de no proteicas).");
        if (v.fistula) ctxMsgs.push("ℹ️ Fístulas: Valorar Zinc extra (10-20 mg/d).");

        if (ctxMsgs.length > 0) {
            alertCtx.style.display = 'block';
            alertCtx.innerHTML = ctxMsgs.join('<br>');
        } else {
            alertCtx.style.display = 'none';
        }

        // 4. Generate Guide & Prescription
        // Update Step text - Detailed Guide
        const kcalMeta = NPT.round(res.kcalTarget, 0);
        document.getElementById('step-kcal-val').innerHTML = `${v.kcalKg} kcal/kg × peso de cálculo = <strong>${kcalMeta} kcal</strong>`;
        document.getElementById('step-start-pct').textContent = `${Math.round(v.startPct * 100)}%`;

        document.getElementById('step-prot-val').innerHTML = `${v.protKg} g/kg → <strong>${NPT.round(res.protDay, 0)} g</strong> (N ${NPT.round(res.nitrogenDay, 1)} g)`;

        document.getElementById('step-gluc-pct').textContent = Math.round(v.pctGluc);
        document.getElementById('step-lip-pct').textContent = 100 - Math.round(v.pctGluc);

        document.getElementById('step-gluc-g').textContent = NPT.round(res.gGlu, 0);
        document.getElementById('step-gluc-ml').textContent = NPT.round(res.mlD50, 0);

        document.getElementById('step-lip-g').textContent = NPT.round(res.gLip, 0);
        document.getElementById('step-lip-ml').textContent = NPT.round(res.mlLip20, 0);

        document.getElementById('step-vol-total').textContent = NPT.round(res.volTotal, 0);
        document.getElementById('step-rate').textContent = NPT.round(res.rate, 0);

        // Generate Template
        const template = App.generateTemplate(v, res, weightCalc, bmi, isObese);
        document.getElementById('prescription-output').value = template;
    },

    generateTemplate: (v, res, weightCalc, bmi, isObese) => {
        const weightStr = isObese ? `PA ${NPT.round(weightCalc, 1)} kg` : `${NPT.round(weightCalc, 1)} kg`;

        return `ORDEN DE NUTRICIÓN PARENTERAL
----------------------------------------
PACIENTE:
Peso Cálculo: ${weightStr} (IMC ${NPT.round(bmi, 1)})
Situación: ${v.stress === 'si' ? 'Sepsis/Estrés' : 'Estándar'} | ${v.refeeding ? 'Riesgo Realimentación' : 'Sin Riesgo Realimentación'}

APORTE DIARIO (Día ${Math.round(v.startPct * 100)}% de la meta):
• Calorías Totales: ${NPT.round(res.kcalDay, 0)} kcal
• Proteínas:        ${NPT.round(res.protDay, 0)} g  (Nitrógeno ${NPT.round(res.nitrogenDay, 1)} g)
• Glucosa:          ${NPT.round(res.gGlu, 0)} g  (${Math.round(v.pctGluc)}% no prot)
• Lípidos:          ${NPT.round(res.gLip, 0)} g  (${100 - Math.round(v.pctGluc)}% no prot)

COMPOSICIÓN DE LA BOLSA:
1. Aminoácidos (${v.aaPct}%):     ${NPT.round(res.mlAA, 0)} mL
2. Dextrosa 50%:          ${NPT.round(res.mlD50, 0)} mL
3. Lípidos 20%:           ${NPT.round(res.mlLip20, 0)} mL

VOLUMEN Y RITMO:
• Volumen Total:    ${NPT.round(res.volTotal, 0)} mL (más aditivos)
• Ritmo de Infusión: ${NPT.round(res.rate, 0)} mL/h (en 24h)

ADITIVOS SUGERIDOS (Ajustar a analítica):
• Na/K: 1-2 mEq/kg/d
• P (Fosfato): 20-40 mmol/d
• Mg: 8-20 mEq/d | Ca: 10-15 mEq/d
• Multivitamínico + Oligoelementos: 1 vial/día
${v.fistula ? '• ZINC EXTRA: 10-20 mg/d (por pérdidas/fístula)' : ''}
${v.refeeding ? '• TIAMINA: 100-200 mg IV (Alerta Realimentación)' : ''}

MONITORIZACIÓN:
• Glucemia 140-180 mg/dL.
• Triglicéridos a las 48-72h (Pausar lípidos si >400).
• Balance Hídrico y Electrolitos diarios al inicio.
`;
    },

    copyPrescription: () => {
        const txt = document.getElementById('prescription-output');
        txt.select();
        navigator.clipboard.writeText(txt.value).then(() => {
            const btn = document.getElementById('btn-copy');
            const original = btn.innerHTML;
            btn.innerHTML = '<span>✅ Copiado</span>';
            setTimeout(() => btn.innerHTML = original, 2000);
        });
    }
};

// Start
document.addEventListener('DOMContentLoaded', App.init);

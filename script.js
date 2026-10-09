const form = document.querySelector("#evaluationForm");
const tbody = document.querySelector("#recordsBody");
const message = document.querySelector("#formMessage");
const search = document.querySelector("#searchInput");
const dateInput = document.querySelector("#evaluationDate");

const today = new Date();
dateInput.value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;

let records = [
  {code:"DEMO-001", date:"2026-10-06", type:"Entrevista psicológica", status:"Registrado", notes:"Registro ficticio para demostrar la interfaz."},
  {code:"DEMO-002", date:"2026-10-07", type:"Evaluación de seguimiento", status:"Pendiente de revisión", notes:"Ejemplo sin datos personales ni clínicos reales."}
];

function safeText(value) {
  return String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
}
function renderRows(filter = "") {
  const normalized = filter.trim().toLowerCase();
  const visible = records.filter(record => record.code.toLowerCase().includes(normalized));
  tbody.innerHTML = visible.length ? visible.map(record => `
    <tr>
      <td>${safeText(record.code)}</td>
      <td>${safeText(record.date)}</td>
      <td>${safeText(record.type)}</td>
      <td><span class="status-pill ${record.status === "Registrado" ? "done" : ""}">${safeText(record.status)}</span></td>
      <td>${safeText(record.notes)}</td>
    </tr>`).join("") : `<tr><td colspan="5">No se encontraron registros.</td></tr>`;
  document.querySelector("#totalCount").textContent = records.length;
  document.querySelector("#pendingCount").textContent = records.filter(r => r.status !== "Registrado").length;
  document.querySelector("#lastUpdate").textContent = "Actualizado";
}
form.addEventListener("submit", event => {
  event.preventDefault();
  const record = {
    code: document.querySelector("#recordCode").value.trim(),
    date: dateInput.value,
    type: document.querySelector("#evaluationType").value,
    status: document.querySelector("#status").value,
    notes: document.querySelector("#notes").value.trim()
  };
  if (!record.code || !record.date || !record.type || !record.notes) {
    message.textContent = "Complete todos los campos obligatorios.";
    return;
  }
  if (records.some(item => item.code.toLowerCase() === record.code.toLowerCase())) {
    message.textContent = "Ese código ya existe. Use uno diferente.";
    document.querySelector("#recordCode").focus();
    return;
  }
  records.unshift(record);
  form.reset();
  dateInput.value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
  message.textContent = "Evaluación de demostración agregada correctamente.";
  renderRows(search.value);
});
search.addEventListener("input", () => renderRows(search.value));
renderRows();

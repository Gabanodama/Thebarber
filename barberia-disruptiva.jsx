import { useState, useEffect, useRef } from "react";

const BARBERS = [
  {
    id: 1,
    name: "Sebastián Mora",
    specialty: "Degradados & Texturas",
    rating: 4.9,
    reviews: 312,
    avatar: "SM",
    color: "#C084FC",
    status: "available",
    delay: -5,
    styles: ["Fade clásico", "Drop fade", "Skin fade", "Texturizado"],
    bio: "10 años moldeando identidades. Especialista en pieles y degradados precisos.",
  },
  {
    id: 2,
    name: "Diego Vargas",
    specialty: "Clásico & Barbas",
    rating: 4.8,
    reviews: 276,
    avatar: "DV",
    color: "#34D399",
    status: "busy",
    delay: 8,
    styles: ["Pompadour", "Slick back", "Barba esculpida", "Afeitado navaja"],
    bio: "Barbero tradicional con visión contemporánea. Maestro del acero.",
  },
  {
    id: 3,
    name: "Camilo Ríos",
    specialty: "Diseños & Creativos",
    rating: 4.7,
    reviews: 198,
    avatar: "CR",
    color: "#FB923C",
    status: "available",
    delay: 0,
    styles: ["Líneas geométricas", "Arte capilar", "360 waves", "Mohawk"],
    bio: "Artista que usa el cabello como lienzo. Cada corte es una obra única.",
  },
];

const SERVICES = [
  { id: 1, name: "Corte + Estilo", duration: 60, price: 45000 },
  { id: 2, name: "Corte + Barba", duration: 60, price: 55000 },
  { id: 3, name: "Afeitado Navaja", duration: 60, price: 35000 },
  { id: 4, name: "Diseño Creativo", duration: 60, price: 65000 },
];

const generateTimeSlots = () => {
  const slots = [];
  for (let h = 8; h <= 19; h++) {
    slots.push(`${h.toString().padStart(2, "0")}:00`);
  }
  return slots;
};

const getWeekDays = () => {
  const today = new Date();
  const days = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    days.push(d);
  }
  return days;
};

const formatPrice = (p) => new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 }).format(p);

const BOOKED = { "1-2025-07-14-09:00": true, "1-2025-07-14-10:00": true, "2-2025-07-14-11:00": true };

export default function BarberiaDisruptiva() {
  const [step, setStep] = useState(0);
  const [selectedBarber, setSelectedBarber] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [selectedDay, setSelectedDay] = useState(0);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [clientPhone, setClientPhone] = useState("");
  const [styleNote, setStyleNote] = useState("");
  const [styleImage, setStyleImage] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [notifSent, setNotifSent] = useState(false);
  const [activeTab, setActiveTab] = useState("book");
  const fileRef = useRef();
  const days = getWeekDays();
  const slots = generateTimeSlots();

  const dayNames = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
  const monthNames = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];

  const isBooked = (barberId, dayIdx, slot) => {
    const d = days[dayIdx];
    const key = `${barberId}-${d.getFullYear()}-${(d.getMonth()+1).toString().padStart(2,"0")}-${d.getDate().toString().padStart(2,"0")}-${slot}`;
    return BOOKED[key] || false;
  };

  const handleConfirm = () => {
    if (!clientName || !clientEmail) return;
    setConfirmed(true);
    setStep(4);
    setTimeout(() => setNotifSent(true), 2000);
  };

  const reset = () => {
    setStep(0); setSelectedBarber(null); setSelectedService(null);
    setSelectedDay(0); setSelectedSlot(null); setClientName("");
    setClientEmail(""); setClientPhone(""); setStyleNote("");
    setStyleImage(null); setConfirmed(false); setNotifSent(false);
  };

  const barber = BARBERS.find(b => b.id === selectedBarber);
  const service = SERVICES.find(s => s.id === selectedService);

  const statusIcon = (delay) => {
    if (delay < 0) return { label: `${Math.abs(delay)} min adelantado`, color: "#34D399", dot: "#34D399" };
    if (delay === 0) return { label: "En horario exacto", color: "#A3A3A3", dot: "#A3A3A3" };
    return { label: `${delay} min de retraso`, color: "#FB923C", dot: "#FB923C" };
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0A0A0A", color: "#F5F5F5", fontFamily: "'DM Sans', system-ui, sans-serif", position: "relative" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input, textarea { background: #1A1A1A; border: 1px solid #2A2A2A; color: #F5F5F5; border-radius: 10px; padding: 12px 16px; width: 100%; font-family: inherit; font-size: 14px; outline: none; transition: border-color 0.2s; }
        input:focus, textarea:focus { border-color: #C084FC; }
        input::placeholder, textarea::placeholder { color: #555; }
        ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #111; } ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
        .slot-btn { background: #141414; border: 1px solid #242424; color: #A3A3A3; border-radius: 8px; padding: 9px 14px; cursor: pointer; font-size: 13px; font-family: inherit; transition: all 0.15s; }
        .slot-btn:hover:not(:disabled) { border-color: #C084FC44; color: #F5F5F5; }
        .slot-btn.selected { background: #C084FC18; border-color: #C084FC; color: #C084FC; }
        .slot-btn:disabled { opacity: 0.3; cursor: not-allowed; text-decoration: line-through; }
        .barber-card { background: #111; border: 1px solid #1E1E1E; border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.2s; }
        .barber-card:hover { border-color: #333; transform: translateY(-2px); }
        .barber-card.selected { border-color: #C084FC; background: #1A1228; }
        .step-pill { display: inline-flex; align-items: center; gap: 6px; background: #161616; border: 1px solid #242424; border-radius: 24px; padding: 6px 14px; font-size: 12px; color: #888; }
        .primary-btn { background: #C084FC; color: #0A0A0A; border: none; border-radius: 12px; padding: 14px 28px; font-size: 15px; font-weight: 600; cursor: pointer; font-family: inherit; transition: all 0.15s; width: 100%; }
        .primary-btn:hover { background: #D8A8FF; }
        .primary-btn:disabled { background: #333; color: #666; cursor: not-allowed; }
        .ghost-btn { background: transparent; border: 1px solid #2A2A2A; color: #888; border-radius: 12px; padding: 12px 20px; font-size: 14px; cursor: pointer; font-family: inherit; transition: all 0.15s; }
        .ghost-btn:hover { border-color: #444; color: #CCC; }
        .tag { background: #1E1E1E; border: 1px solid #2A2A2A; border-radius: 6px; padding: 4px 10px; font-size: 12px; color: #888; }
        .nav-tab { background: transparent; border: none; color: #666; font-family: inherit; font-size: 14px; font-weight: 500; padding: 10px 20px; cursor: pointer; border-radius: 8px; transition: all 0.15s; }
        .nav-tab.active { background: #1A1A1A; color: #F5F5F5; }
        .pulse { animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        .fade-in { animation: fadeIn 0.4s ease-out; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .service-card { background: #111; border: 1px solid #1E1E1E; border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.15s; }
        .service-card:hover { border-color: #333; }
        .service-card.selected { border-color: #C084FC; background: #1A1228; }
        .check-anim { animation: checkIn 0.5s ease-out; }
        @keyframes checkIn { 0%{transform:scale(0);opacity:0} 70%{transform:scale(1.1)} 100%{transform:scale(1);opacity:1} }
      `}</style>

      {/* Header */}
      <header style={{ borderBottom: "1px solid #161616", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, background: "#0A0A0A", zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 32, height: 32, background: "#C084FC18", border: "1px solid #C084FC44", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 14 }}>✂</span>
          </div>
          <div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, letterSpacing: "-0.3px" }}>BARBERÍA <span style={{ color: "#C084FC" }}>DISRUPTIVA</span></div>
            <div style={{ fontSize: 11, color: "#555", letterSpacing: "0.5px" }}>MEDELLÍN · EST. 2024</div>
          </div>
        </div>
        <nav style={{ display: "flex", gap: 4 }}>
          {["book","live","profile"].map(t => (
            <button key={t} className={`nav-tab ${activeTab===t?"active":""}`} onClick={() => { setActiveTab(t); if(t==="book") setStep(0); }}>
              {t === "book" ? "Agendar" : t === "live" ? "📍 En Vivo" : "Mi Perfil"}
            </button>
          ))}
        </nav>
      </header>

      <main style={{ maxWidth: 680, margin: "0 auto", padding: "32px 20px" }}>

        {/* ── LIVE STATUS TAB ── */}
        {activeTab === "live" && (
          <div className="fade-in">
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Estado en Tiempo Real</div>
              <div style={{ color: "#666", fontSize: 14 }}>Sé si salir de casa o esperar un poco más.</div>
            </div>
            {BARBERS.map(b => {
              const st = statusIcon(b.delay);
              return (
                <div key={b.id} style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 16, padding: 20, marginBottom: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                    <div style={{ width: 48, height: 48, borderRadius: "50%", background: b.color + "22", border: `2px solid ${b.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 14, color: b.color }}>{b.avatar}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{b.name}</div>
                      <div style={{ fontSize: 12, color: "#666" }}>{b.specialty}</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end", marginBottom: 4 }}>
                        <div className={b.status === "available" ? "pulse" : ""} style={{ width: 8, height: 8, borderRadius: "50%", background: st.dot }} />
                        <span style={{ fontSize: 13, color: st.color, fontWeight: 500 }}>{st.label}</span>
                      </div>
                      <div style={{ fontSize: 12, color: "#555" }}>{b.status === "available" ? "Disponible ahora" : "En corte"}</div>
                    </div>
                  </div>
                  {b.delay !== 0 && (
                    <div style={{ marginTop: 12, background: "#161616", borderRadius: 10, padding: "10px 14px", fontSize: 12, color: "#888" }}>
                      💡 {b.delay > 0 ? `Tu barbero lleva ${b.delay} min de retraso — podrías salir más tarde.` : `Va ${Math.abs(b.delay)} min adelantado — mejor llega ya.`}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── PROFILE TAB ── */}
        {activeTab === "profile" && (
          <div className="fade-in">
            <div style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 16, padding: 28, textAlign: "center", marginBottom: 16 }}>
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: "#C084FC22", border: "2px solid #C084FC44", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px", fontSize: 28 }}>👤</div>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Tu Perfil de Estilo</div>
              <div style={{ color: "#666", fontSize: 14 }}>Sube referencias para que tu barbero llegue preparado.</div>
            </div>
            <div style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 16, padding: 20, marginBottom: 12 }}>
              <div style={{ fontSize: 13, color: "#888", marginBottom: 12, fontWeight: 500, letterSpacing: "0.5px" }}>ÚLTIMA VISITA</div>
              <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                <div style={{ width: 64, height: 80, borderRadius: 10, background: "#1A1A1A", border: "1px dashed #2A2A2A", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", cursor: "pointer", gap: 4 }}>
                  <span style={{ fontSize: 20 }}>📷</span>
                  <span style={{ fontSize: 10, color: "#555" }}>Subir foto</span>
                </div>
                <div style={{ fontSize: 13, color: "#666", lineHeight: 1.6 }}>Sube la foto de tu último corte o del estilo que quieres. Tu barbero la revisará antes de que llegues.</div>
              </div>
            </div>
            <div style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 16, padding: 20 }}>
              <div style={{ fontSize: 13, color: "#888", marginBottom: 12, fontWeight: 500, letterSpacing: "0.5px" }}>PREFERENCIAS</div>
              {["Degradado en los lados", "Textura en la parte superior", "Sin arreglo de ceja"].map((p, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < 2 ? "1px solid #1A1A1A" : "none" }}>
                  <div style={{ width: 18, height: 18, borderRadius: 4, background: "#C084FC22", border: "1px solid #C084FC44", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, color: "#C084FC" }}>✓</div>
                  <span style={{ fontSize: 14, color: "#CCC" }}>{p}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── BOOK TAB ── */}
        {activeTab === "book" && (
          <div>
            {/* Confirmed */}
            {step === 4 && (
              <div className="fade-in" style={{ textAlign: "center", padding: "40px 20px" }}>
                <div className="check-anim" style={{ width: 80, height: 80, borderRadius: "50%", background: "#34D39922", border: "2px solid #34D39944", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px", fontSize: 36 }}>✓</div>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 26, fontWeight: 700, marginBottom: 8 }}>¡Cita Confirmada!</div>
                <div style={{ color: "#666", fontSize: 15, marginBottom: 32 }}>Te esperamos, {clientName.split(" ")[0]}.</div>
                <div style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 16, padding: 20, textAlign: "left", marginBottom: 16 }}>
                  <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                    <div style={{ width: 44, height: 44, borderRadius: "50%", background: barber?.color + "22", border: `1px solid ${barber?.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 13, color: barber?.color, flexShrink: 0 }}>{barber?.avatar}</div>
                    <div>
                      <div style={{ fontWeight: 600, marginBottom: 2 }}>{barber?.name}</div>
                      <div style={{ fontSize: 13, color: "#888", marginBottom: 6 }}>{service?.name}</div>
                      <div style={{ fontSize: 13, color: "#C084FC", fontWeight: 500 }}>
                        {days[selectedDay].toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" })} · {selectedSlot}
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ background: "#0F1A0F", border: "1px solid #1E2E1E", borderRadius: 12, padding: "12px 16px", marginBottom: 24, display: "flex", alignItems: "center", gap: 10 }}>
                  <div className={notifSent ? "" : "pulse"} style={{ width: 8, height: 8, borderRadius: "50%", background: notifSent ? "#34D399" : "#FB923C", flexShrink: 0 }} />
                  <span style={{ fontSize: 13, color: notifSent ? "#34D399" : "#FB923C" }}>
                    {notifSent ? `✓ Confirmación enviada a ${clientEmail}` : "Enviando confirmación..."}
                  </span>
                </div>
                <div style={{ background: "#0D0D14", border: "1px solid #1E1E2E", borderRadius: 12, padding: "12px 16px", marginBottom: 24, fontSize: 13, color: "#888", display: "flex", gap: 8 }}>
                  <span>🔔</span>
                  <span>Recibirás un recordatorio 1 hora antes vía SMS y Email.</span>
                </div>
                <button className="ghost-btn" style={{ width: "100%" }} onClick={reset}>Agendar otra cita</button>
              </div>
            )}

            {step < 4 && (
              <>
                {/* Step indicator */}
                <div style={{ display: "flex", gap: 8, marginBottom: 32 }}>
                  {["Barbero", "Servicio", "Horario", "Datos"].map((s, i) => (
                    <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                      <div style={{ height: 3, borderRadius: 2, background: i <= step ? "#C084FC" : "#1E1E1E", transition: "background 0.3s" }} />
                      <span style={{ fontSize: 11, color: i === step ? "#C084FC" : "#555", fontWeight: i === step ? 500 : 400 }}>{s}</span>
                    </div>
                  ))}
                </div>

                {/* STEP 0 — Select Barber */}
                {step === 0 && (
                  <div className="fade-in">
                    <div style={{ marginBottom: 24 }}>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Elige tu barbero</div>
                      <div style={{ color: "#666", fontSize: 14 }}>Cada uno con su propio estilo y disponibilidad en tiempo real.</div>
                    </div>
                    {BARBERS.map(b => {
                      const st = statusIcon(b.delay);
                      return (
                        <div key={b.id} className={`barber-card ${selectedBarber===b.id?"selected":""}`} style={{ marginBottom: 12 }} onClick={() => setSelectedBarber(b.id)}>
                          <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                            <div style={{ width: 52, height: 52, borderRadius: "50%", background: b.color + "22", border: `2px solid ${b.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: b.color, flexShrink: 0 }}>{b.avatar}</div>
                            <div style={{ flex: 1 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                                <div>
                                  <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 2 }}>{b.name}</div>
                                  <div style={{ fontSize: 13, color: "#888" }}>{b.specialty}</div>
                                </div>
                                <div style={{ textAlign: "right" }}>
                                  <div style={{ fontSize: 13, fontWeight: 500, color: "#F5F5F5" }}>⭐ {b.rating}</div>
                                  <div style={{ fontSize: 11, color: "#555" }}>{b.reviews} reseñas</div>
                                </div>
                              </div>
                              <div style={{ fontSize: 13, color: "#666", marginBottom: 10 }}>{b.bio}</div>
                              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
                                {b.styles.map(s => <span key={s} className="tag">{s}</span>)}
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                <div className={b.status === "available" ? "pulse" : ""} style={{ width: 7, height: 7, borderRadius: "50%", background: st.dot }} />
                                <span style={{ fontSize: 12, color: st.color }}>{st.label}</span>
                              </div>
                            </div>
                          </div>
                          {selectedBarber === b.id && (
                            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #2A1A40", display: "flex", justifyContent: "flex-end" }}>
                              <button className="primary-btn" style={{ width: "auto", padding: "10px 24px" }} onClick={() => setStep(1)}>Continuar →</button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* STEP 1 — Select Service */}
                {step === 1 && (
                  <div className="fade-in">
                    <div style={{ marginBottom: 24 }}>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Servicio</div>
                      <div style={{ color: "#666", fontSize: 14 }}>Todos los servicios duran exactamente 60 minutos.</div>
                    </div>
                    {SERVICES.map(s => (
                      <div key={s.id} className={`service-card ${selectedService===s.id?"selected":""}`} style={{ marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }} onClick={() => setSelectedService(s.id)}>
                        <div>
                          <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 2 }}>{s.name}</div>
                          <div style={{ fontSize: 12, color: "#666" }}>⏱ 60 min</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: selectedService===s.id ? "#C084FC" : "#F5F5F5" }}>{formatPrice(s.price)}</div>
                          {selectedService === s.id && <div style={{ fontSize: 11, color: "#C084FC" }}>✓ Seleccionado</div>}
                        </div>
                      </div>
                    ))}
                    <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
                      <button className="ghost-btn" onClick={() => setStep(0)}>← Volver</button>
                      <button className="primary-btn" disabled={!selectedService} onClick={() => setStep(2)}>Continuar →</button>
                    </div>
                  </div>
                )}

                {/* STEP 2 — Select Date & Time */}
                {step === 2 && (
                  <div className="fade-in">
                    <div style={{ marginBottom: 24 }}>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Fecha y Hora</div>
                      <div style={{ color: "#666", fontSize: 14 }}>Selecciona cuando quieres verte brutal.</div>
                    </div>
                    <div style={{ display: "flex", gap: 8, marginBottom: 24, overflowX: "auto", paddingBottom: 4 }}>
                      {days.map((d, i) => (
                        <button key={i} onClick={() => { setSelectedDay(i); setSelectedSlot(null); }} style={{ flexShrink: 0, background: selectedDay===i ? "#C084FC18" : "#111", border: `1px solid ${selectedDay===i ? "#C084FC" : "#1E1E1E"}`, borderRadius: 12, padding: "12px 14px", cursor: "pointer", textAlign: "center", transition: "all 0.15s", minWidth: 58 }}>
                          <div style={{ fontSize: 11, color: selectedDay===i ? "#C084FC" : "#666", marginBottom: 4 }}>{dayNames[d.getDay()]}</div>
                          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 700, color: selectedDay===i ? "#C084FC" : "#F5F5F5" }}>{d.getDate()}</div>
                          <div style={{ fontSize: 10, color: selectedDay===i ? "#C084FC99" : "#555" }}>{monthNames[d.getMonth()]}</div>
                        </button>
                      ))}
                    </div>
                    <div style={{ fontSize: 13, color: "#888", marginBottom: 12, fontWeight: 500, letterSpacing: "0.5px" }}>HORARIOS DISPONIBLES</div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginBottom: 24 }}>
                      {slots.map(slot => {
                        const booked = isBooked(selectedBarber, selectedDay, slot);
                        return (
                          <button key={slot} disabled={booked} className={`slot-btn ${selectedSlot===slot?"selected":""}`} onClick={() => setSelectedSlot(slot)}>
                            {slot}{booked ? " ✕" : ""}
                          </button>
                        );
                      })}
                    </div>
                    <div style={{ display: "flex", gap: 10 }}>
                      <button className="ghost-btn" onClick={() => setStep(1)}>← Volver</button>
                      <button className="primary-btn" disabled={!selectedSlot} onClick={() => setStep(3)}>Continuar →</button>
                    </div>
                  </div>
                )}

                {/* STEP 3 — Client Details + Style Upload */}
                {step === 3 && (
                  <div className="fade-in">
                    <div style={{ marginBottom: 24 }}>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Tus Datos</div>
                      <div style={{ color: "#666", fontSize: 14 }}>Casi listo. Cuéntanos un poco más.</div>
                    </div>

                    {/* Booking Summary */}
                    <div style={{ background: "#0F0A1A", border: "1px solid #2A1A40", borderRadius: 12, padding: "14px 16px", marginBottom: 20 }}>
                      <div style={{ fontSize: 12, color: "#888", marginBottom: 8, letterSpacing: "0.5px" }}>RESUMEN DE TU CITA</div>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#CCC" }}>
                        <span>{barber?.name} · {service?.name}</span>
                        <span style={{ color: "#C084FC", fontWeight: 600 }}>{formatPrice(service?.price || 0)}</span>
                      </div>
                      <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                        {days[selectedDay].toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" })} a las {selectedSlot}
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
                      <input placeholder="Nombre completo *" value={clientName} onChange={e => setClientName(e.target.value)} />
                      <input placeholder="Email *" type="email" value={clientEmail} onChange={e => setClientEmail(e.target.value)} />
                      <input placeholder="WhatsApp / Teléfono" value={clientPhone} onChange={e => setClientPhone(e.target.value)} />
                    </div>

                    {/* Style Upload */}
                    <div style={{ background: "#111", border: "1px solid #1E1E1E", borderRadius: 14, padding: 16, marginBottom: 20 }}>
                      <div style={{ fontWeight: 500, marginBottom: 4, fontSize: 14 }}>📸 Perfil de Estilo <span style={{ fontSize: 12, color: "#666", fontWeight: 400 }}>(opcional)</span></div>
                      <div style={{ fontSize: 13, color: "#666", marginBottom: 12 }}>Sube la referencia de tu corte ideal. {barber?.name} lo revisará antes de que llegues.</div>
                      {styleImage ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <img src={styleImage} alt="Referencia de estilo" style={{ width: 60, height: 74, objectFit: "cover", borderRadius: 8 }} />
                          <button className="ghost-btn" style={{ fontSize: 13 }} onClick={() => setStyleImage(null)}>✕ Quitar foto</button>
                        </div>
                      ) : (
                        <div onClick={() => fileRef.current.click()} style={{ border: "1px dashed #2A2A2A", borderRadius: 10, padding: "18px", textAlign: "center", cursor: "pointer", transition: "border-color 0.15s" }}>
                          <div style={{ fontSize: 24, marginBottom: 6 }}>📁</div>
                          <div style={{ fontSize: 13, color: "#888" }}>Toca para subir foto</div>
                          <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>JPG, PNG hasta 10MB</div>
                        </div>
                      )}
                      <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={e => { if(e.target.files[0]) setStyleImage(URL.createObjectURL(e.target.files[0])); }} />
                      <textarea placeholder="Describe tu estilo o añade notas para tu barbero..." value={styleNote} onChange={e => setStyleNote(e.target.value)} style={{ marginTop: 10, height: 80, resize: "none" }} />
                    </div>

                    <div style={{ display: "flex", gap: 10 }}>
                      <button className="ghost-btn" onClick={() => setStep(2)}>← Volver</button>
                      <button className="primary-btn" disabled={!clientName || !clientEmail} onClick={handleConfirm}>Confirmar Cita</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

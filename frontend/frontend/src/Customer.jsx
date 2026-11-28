import { useState } from "react";
import { CalendarDays, CarFront, Plus, ShoppingBag, Wrench } from "lucide-react";
import { FormField, Modal } from "./components";
import { statuses, sum } from "./format";
import { request } from "./api";
import { useRemote } from "./useRemote";

const fields = [
  ["make", "Marka"], ["model", "Model"], ["year", "Ishlab chiqarilgan yil", "number"],
  ["engine", "Dvigatel hajmi"], ["fuel", "Yoqilg‘i turi"], ["plate", "Davlat raqami"],
  ["mileage", "Masofa (km)", "number"], ["image", "Rasm havolasi", "url"],
];
const dateDisplay = new Intl.DateTimeFormat("uz-UZ", {
  dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Tashkent",
});

export function CustomerModal({ modal, close, vehicles, source, run, me, go, openModal, pending }) {
  const booking = modal.type === "booking";
  const vehicle = modal.type === "vehicle";
  const chosen = modal.item;
  const catalog = source.data;
  const [vehicleId, setVehicleId] = useState(String(modal.vehicleId || ""));
  const [serviceId, setServiceId] = useState(String(booking ? chosen?.id || "" : ""));
  const [day, setDay] = useState("");
  const [start, setStart] = useState("");
  const today = new Intl.DateTimeFormat("sv-SE", { dateStyle: "short", timeZone: "Asia/Tashkent" }).format(new Date());
  const selectedMake = vehicles.data?.find((item) => String(item.id) === vehicleId)?.make.toLowerCase();
  const services = (catalog?.services || []).filter((item) => item.available);
  const availableServices = services.filter((item) => !selectedMake || !item.make || item.make.toLowerCase() === selectedMake);
  const selectedService = availableServices.some((item) => String(item.id) === serviceId) ? serviceId : "";
  const slots = useRemote("/bookings/slots", { vehicle_id: vehicleId, service_id: selectedService, day },
    Boolean(booking && vehicleId && selectedService && day));
  const canBook = slots.data?.includes(start);
  function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (booking) {
      if (!canBook) return;
      values.vehicle_id = Number(vehicleId);
      values.service_id = Number(selectedService);
      values.starts_at = start;
    } else {
      values.year = Number(values.year);
      values.mileage = Number(values.mileage);
      values.image ||= null;
    }
    run(async () => {
      let saved;
      try {
        saved = await request(booking ? "/bookings" : chosen ? `/vehicles/${chosen.id}` : "/vehicles",
          vehicle && chosen ? "put" : "post", values);
      } catch (error) {
        if (booking) {
          setStart("");
          slots.reload();
        }
        throw error;
      }
      if (vehicle) vehicles.reload();
      if (modal.returnToBooking) {
        openModal({ ...modal.returnToBooking, vehicleId: saved.id });
      } else {
        close();
        if (booking) go("orders");
      }
    }, booking ? "Yozilish qabul qilindi" : "Avtomobil saqlandi");
  }

  if (modal.type === "maintenance") return <Maintenance item={chosen} close={close} run={run} />;
  if (modal.type === "service" && !chosen.available) return <Modal title={chosen.name} close={close}>
    <p>{chosen.description}</p><p>{sum(chosen.price)} · Hozircha bron yopiq.</p>
  </Modal>;

  return <Modal title={booking ? "Avtoservisga yozilish" : chosen ? "Avtomobilni tahrirlash" : "Avtomobil qo‘shish"} close={close}>
    {booking && !vehicles.data?.length ? <><p>{vehicles.error || (vehicles.loading ? "Avtomobillar yuklanmoqda…" : "Yozilish uchun avval avtomobil qo‘shing.")}</p>
      {vehicles.data && <button className="secondary" onClick={() => openModal({ type: "vehicle", returnToBooking: modal })}>Avtomobil qo‘shish</button>}</>
      : booking && !catalog ? <p role="status">{source.error || "Xizmatlar yuklanmoqda…"}</p>
      : booking && !services.length ? <p>Hozircha yozilish uchun ochiq xizmatlar mavjud emas.</p>
      : <form onSubmit={submit}>
        {booking ? <>
          <label>Avtomobil<select value={vehicleId} onChange={(event) => { setVehicleId(event.target.value); setStart(""); }} required><option value="">Tanlang</option>{vehicles.data.map((item) => <option key={item.id} value={item.id}>{item.make} {item.model} · {item.plate}</option>)}</select></label>
          <label>Xizmat<select value={selectedService} onChange={(event) => { setServiceId(event.target.value); setStart(""); }} required><option value="">Tanlang</option>{availableServices.map((item) => <option key={item.id} value={item.id}>{item.name} · {sum(item.price)}</option>)}</select></label>
          <label>Sana<input type="date" min={today} value={day} onChange={(event) => { setDay(event.target.value); setStart(""); }} required /></label>
          {slots.loading && <p role="status">Bo‘sh vaqtlar yuklanmoqda…</p>}
          {slots.error && <p role="alert">{slots.error} <button type="button" className="link-button" onClick={slots.reload}>Qayta urinish</button></p>}
          {slots.data && <fieldset className="booking-slots"><legend>Bo‘sh vaqtlar (Buxoro vaqti)</legend>
            {slots.data.length ? <div className="actions">{slots.data.map((slot) =>
              <button type="button" key={slot} className={slot === start ? "primary" : "secondary"}
                aria-pressed={slot === start} onClick={() => setStart(slot)}>{slot.slice(11, 16)}</button>
            )}</div> : <p>Bu sanada bo‘sh vaqt yo‘q. Boshqa sanani tanlang.</p>}
          </fieldset>}
          <FormField name="phone" label="Telefon" type="tel" value={me?.phone} pattern="[+]?[0-9]{7,15}" />
          <label>Muammo haqida izoh<textarea name="notes" maxLength={1200} rows={3} /></label>
        </> : <div className="form-grid">{fields.map(([name, label, type]) => <FormField key={name} name={name} label={label}
          type={type} value={chosen?.[name]} min={name === "year" ? 1900 : name === "mileage" ? 0 : undefined}
          required={name !== "image"} />)}</div>}
        <button className="primary" disabled={pending || (booking && !canBook)}>{booking ? "Yozilishni tasdiqlash" : "Saqlash"}</button>
      </form>}
  </Modal>;
}

function Maintenance({ item, close, run }) {
  const records = useRemote(`/vehicles/${item.id}/maintenance`);
  const rows = records.data || [];
  const next = rows.map((row) => row.next_on).filter(Boolean).sort()[0];
  const recommended = useRemote(`/vehicles/${item.id}/recommendations`);
  function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    values.next_on ||= null;
    values.cost = Number(values.cost || 0);
    values.oil_change = values.oil_change === "on";
    run(async () => {
      await request(`/vehicles/${item.id}/maintenance`, "post", values);
      form.reset();
      records.reload();
    }, "Texnik xizmat yozuvi saqlandi");
  }
  return <Modal title={`${item.make} ${item.model} · Texnik tarix`} close={close}>
    {records.error && <p role="alert">{records.error}</p>}
    {rows.length > 0 && <div className="panel history"><p>Jami xarajat · {sum(rows.reduce((total, row) => total + row.cost, 0))}</p>
      <p>So‘nggi moy almashtirish · {rows.find((row) => row.oil_change)?.performed_on || "—"}</p>
      <p>Texnik xizmat eslatmasi · {next || "—"}</p>
      {rows.map((row) => <p key={row.id}>{row.performed_on} · {row.title} · {sum(row.cost)}</p>)}
    </div>}
    {recommended.data?.services.length > 0 && <p>Mos xizmatlar · {recommended.data.services.map((row) => row.name).join(", ")}</p>}
    {recommended.data?.products.length > 0 && <p>Mos mahsulotlar · {recommended.data.products.map((row) => row.name).join(", ")}</p>}
    <form onSubmit={submit}>
      <FormField name="title" label="Xizmat nomi" />
      <div className="form-grid"><FormField name="performed_on" label="Bajarilgan sana" type="date" />
        <FormField name="next_on" label="Keyingi xizmat sanasi" type="date" required={false} /></div>
      <FormField name="cost" label="Xarajat (so‘m)" type="number" min={0} required={false} />
      <label className="checkbox"><input name="oil_change" type="checkbox" /> Moy almashtirildi</label>
      <button className="primary">Tarixga qo‘shish</button>
    </form>
  </Modal>;
}

export function Profile({ me, vehicles, modal, run, setLanguage, language, setTheme, theme, go, pending }) {
  const telegramUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
  const photo = telegramUser?.photo_url;
  const notices = useRemote("/notifications", undefined, Boolean(me.data));
  function submit(event) {
    event.preventDefault();
    const input = String(new FormData(event.currentTarget).get("phone"));
    const phone = input.startsWith("+") ? input
      : input.length === 9 ? `+998${input}` : input ? `+${input}` : null;
    run(async () => {
      await request("/me", "patch", { phone });
      me.updateData({ phone });
    }, "Telefon raqami saqlandi");
  }
  function changeLanguage(event) {
    const next = event.target.value;
    run(async () => {
      await request("/me", "patch", { language: next });
      setLanguage(next);
      me.updateData({ language: next });
    }, "Til saqlandi");
  }
  return <section className="view">
    <div className="section-heading"><div><p className="eyebrow">Shaxsiy kabinet</p><h1>Profil</h1></div>
      {me.data?.is_admin && <button className="secondary" onClick={() => go("admin")}>Boshqaruv paneli</button>}</div>
    {me.error && <div className="empty" role="alert">{me.error}</div>}
    {me.data && <><div className="profile-grid"><div className="panel">
      <div className="profile-name">{photo?.startsWith("https://") ? <img src={photo} alt="" /> : <span>{me.data.first_name[0]}</span>}
        <div><h2>{me.data.first_name}</h2>{me.data.username && <p>@{me.data.username}</p>}
          {Number.isSafeInteger(telegramUser?.id) && <p>Telegram ID: {telegramUser.id}</p>}</div></div>
      <form onSubmit={submit}><FormField name="phone" label="Telefon" type="tel" value={me.data.phone} required={false} pattern="[+]?[0-9]{7,15}" placeholder="+998901234567" autoComplete="tel" />
        <button className="primary" disabled={pending}>Telefonni saqlash</button></form>
      <div className="profile-preferences">
        <label>Til<select value={language} disabled={pending} onChange={changeLanguage}><option value="uz">O‘zbekcha</option><option value="ru">Русский</option><option value="en">English</option></select></label>
        <label>Mavzu<select value={theme} onChange={(event) => setTheme(event.target.value)}><option value="dark">Qorong‘i</option><option value="light">Yorug‘</option></select></label>
      </div>
      </div><div className="panel"><h2>Bildirishnomalar</h2>{notices.data?.length
        ? notices.data.map((notice) => <p key={notice.id}>{notice.message}</p>) : <p>Yangi bildirishnomalar yo‘q.</p>}
        <div className="actions"><button className="secondary" onClick={() => go("orders")}>Buyurtmalar tarixi</button>
          <button className="secondary" onClick={() => modal({ type: "favorites" })}>Sevimli mahsulotlar</button></div></div></div>
      <div className="section-heading middle"><h2>Mening avtomobillarim</h2><button className="primary" onClick={() => modal({ type: "vehicle" })}><Plus size={17} /> Avtomobil qo‘shish</button></div>
      {vehicles.error && <p role="alert">{vehicles.error}</p>}
      {!vehicles.loading && !vehicles.error && !vehicles.data?.length && <p className="empty"><CarFront /> Avtomobil qo‘shilmagan.</p>}
      <div className="cards">{vehicles.data?.map((item) => <div className="panel vehicle" key={item.id}>
        {item.image && <img src={item.image} alt={`${item.make} ${item.model}`} loading="lazy" onError={(event) => { event.currentTarget.hidden = true; }} />}
        <CarFront /><h3>{item.make} {item.model}</h3><p>{item.year} · {item.plate} · {item.mileage.toLocaleString()} km</p>
        <div className="actions"><button className="secondary" onClick={() => modal({ type: "maintenance", item })}>Texnik tarix</button>
          <button className="secondary" onClick={() => modal({ type: "vehicle", item })}>Tahrirlash</button></div>
      </div>)}</div></>}
  </section>;
}

export function Orders() {
  const bookings = useRemote("/bookings");
  const orders = useRemote("/orders");
  return <section className="view"><div className="section-heading"><div><p className="eyebrow">Shaxsiy kabinet</p><h1>Buyurtmalar</h1></div></div>
    {(bookings.error || orders.error) && <p className="empty" role="alert">{bookings.error || orders.error}</p>}
    <div className="profile-grid">
      <div className="panel history"><h2><CalendarDays size={20} /> Avtoservis yozilishlari</h2>
        {bookings.data?.map((row) => <article key={row.id}>
          <div><strong>{row.service_name || "Avtoservis xizmati"}</strong><p><Wrench size={15} /> #{row.id} · {dateDisplay.format(new Date(row.starts_at))}</p></div>
          <span>{row.status === "new" ? "Admin tasdig‘i kutilmoqda" : statuses[row.status]}</span>
        </article>)}
        {!bookings.loading && !bookings.error && !bookings.data?.length && <p>Yozilishlar mavjud emas.</p>}</div>
      <div className="panel history"><h2><ShoppingBag size={20} /> Ehtiyot qismlar buyurtmalari</h2>
        {orders.data?.map((row) => <article key={row.id}><div>#{row.id} · {sum(row.total)}<p>{row.items.map((item) => `${item.name} × ${item.quantity}`).join(", ")}</p></div><span>{statuses[row.status]}</span></article>)}
        {!orders.loading && !orders.error && !orders.data?.length && <p>Buyurtmalar mavjud emas.</p>}</div>
    </div>
  </section>;
}

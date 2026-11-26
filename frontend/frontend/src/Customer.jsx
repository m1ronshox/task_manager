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

export function CustomerModal({ modal, close, vehicles, source, run, me, go }) {
  const booking = modal.type === "booking";
  const vehicle = modal.type === "vehicle";
  const chosen = modal.item;
  const catalog = source.data;
  const [vehicleId, setVehicleId] = useState("");
  const selectedMake = vehicles.data?.find((item) => String(item.id) === vehicleId)?.make.toLowerCase();
  const services = (catalog?.services || []).filter((item) => item.available);
  const availableServices = services.filter((item) => !selectedMake || !item.make || item.make.toLowerCase() === selectedMake);
  function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (booking) {
      values.vehicle_id = Number(values.vehicle_id);
      values.service_id = Number(values.service_id);
      values.starts_at = new Date(`${values.starts_at}:00+05:00`).toISOString();
    } else {
      values.year = Number(values.year);
      values.mileage = Number(values.mileage);
      values.image ||= null;
    }
    run(async () => {
      await request(booking ? "/bookings" : chosen ? `/vehicles/${chosen.id}` : "/vehicles",
        vehicle && chosen ? "put" : "post", values);
      if (vehicle) vehicles.reload();
      close();
      if (booking) go("orders");
    }, booking ? "Yozilish qabul qilindi" : "Avtomobil saqlandi");
  }

  if (modal.type === "maintenance") return <Maintenance item={chosen} close={close} run={run} />;
  if (modal.type === "service" && !chosen.available) return <Modal title={chosen.name} close={close}>
    <p>{chosen.description}</p><p>{sum(chosen.price)} · Hozircha bron yopiq.</p>
  </Modal>;

  return <Modal title={booking ? "Avtoservisga yozilish" : chosen ? "Avtomobilni tahrirlash" : "Avtomobil qo‘shish"} close={close}>
    {booking && !vehicles.data?.length ? <><p>{vehicles.error || (vehicles.loading ? "Avtomobillar yuklanmoqda…" : "Yozilish uchun avval avtomobil qo‘shing.")}</p>
      <button className="secondary" onClick={() => { close(); go("profile"); }}>Profilga o‘tish</button></>
      : booking && !catalog ? <p role="status">{source.error || "Xizmatlar yuklanmoqda…"}</p>
      : booking && !services.length ? <p>Hozircha yozilish uchun ochiq xizmatlar mavjud emas.</p>
      : <form onSubmit={submit}>
        {booking ? <>
          <label>Avtomobil<select name="vehicle_id" value={vehicleId} onChange={(event) => setVehicleId(event.target.value)} required><option value="">Tanlang</option>{vehicles.data.map((item) => <option key={item.id} value={item.id}>{item.make} {item.model} · {item.plate}</option>)}</select></label>
          <label>Xizmat<select name="service_id" defaultValue={chosen?.id || ""} required><option value="">Tanlang</option>{availableServices.map((item) => <option key={item.id} value={item.id}>{item.name} · {sum(item.price)}</option>)}</select></label>
          <FormField name="starts_at" label="Sana va vaqt (Buxoro vaqti)" type="datetime-local" />
          <FormField name="phone" label="Telefon" type="tel" value={me?.phone} pattern="[+]?[0-9]{7,15}" />
          <label>Muammo haqida izoh<textarea name="notes" maxLength={1200} rows={3} /></label>
        </> : <div className="form-grid">{fields.map(([name, label, type]) => <FormField key={name} name={name} label={label}
          type={type} value={chosen?.[name]} min={name === "year" ? 1900 : name === "mileage" ? 0 : undefined}
          required={name !== "image"} />)}</div>}
        <button className="primary">{booking ? "Yozilishni tasdiqlash" : "Saqlash"}</button>
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

export function Profile({ me, vehicles, modal, run, setLanguage, language, setTheme, theme, go }) {
  const telegramUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
  const photo = telegramUser?.photo_url;
  const notices = useRemote("/notifications", undefined, Boolean(me.data));
  function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    values.phone ||= null;
    run(async () => {
      await request("/me", "put", values);
      setLanguage(values.language);
      me.reload();
    }, "Profil sozlamalari yangilandi");
  }
  return <section className="view">
    <div className="section-heading"><div><p className="eyebrow">Shaxsiy kabinet</p><h1>Profil</h1></div>
      {me.data?.is_admin && <button className="secondary" onClick={() => go("admin")}>Boshqaruv paneli</button>}</div>
    {me.error && <div className="empty" role="alert">{me.error}</div>}
    {me.data && <><div className="profile-grid"><div className="panel">
      <div className="profile-name">{photo?.startsWith("https://") ? <img src={photo} alt="" /> : <span>{me.data.first_name[0]}</span>}
        <div><h2>{me.data.first_name}</h2>{me.data.username && <p>@{me.data.username}</p>}
          {Number.isSafeInteger(telegramUser?.id) && <p>Telegram ID: {telegramUser.id}</p>}</div></div>
      <form onSubmit={submit}><FormField name="phone" label="Telefon" type="tel" value={me.data.phone} required={false} pattern="[+]?[0-9]{7,15}" />
        <label>Til<select name="language" defaultValue={me.data.language || language}><option value="uz">O‘zbekcha</option><option value="ru">Русский</option><option value="en">English</option></select></label>
        <label>Mavzu<select value={theme} onChange={(event) => setTheme(event.target.value)}><option value="dark">Qorong‘i</option><option value="light">Yorug‘</option></select></label>
        <button className="primary">Sozlamalarni saqlash</button></form>
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
        {bookings.data?.map((row) => <article key={row.id}><span><Wrench size={15} /> #{row.id} · {dateDisplay.format(new Date(row.starts_at))}</span><span>{statuses[row.status]}</span></article>)}
        {!bookings.loading && !bookings.error && !bookings.data?.length && <p>Yozilishlar mavjud emas.</p>}</div>
      <div className="panel history"><h2><ShoppingBag size={20} /> Ehtiyot qismlar buyurtmalari</h2>
        {orders.data?.map((row) => <article key={row.id}><div>#{row.id} · {sum(row.total)}<p>{row.items.map((item) => `${item.name} × ${item.quantity}`).join(", ")}</p></div><span>{statuses[row.status]}</span></article>)}
        {!orders.loading && !orders.error && !orders.data?.length && <p>Buyurtmalar mavjud emas.</p>}</div>
    </div>
  </section>;
}

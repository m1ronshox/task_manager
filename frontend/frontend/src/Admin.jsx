import { useState } from "react";
import { BarChart3, Pencil, Plus } from "lucide-react";
import { FormField, Modal } from "./components";
import { statuses, sum } from "./format";
import { request } from "./api";

const sections = {
  dashboard: "Dashboard", users: "Foydalanuvchilar", services: "Xizmatlar",
  "service-categories": "Xizmat kategoriyalari", products: "Mahsulotlar",
  "product-categories": "Mahsulot kategoriyalari", orders: "Buyurtmalar", bookings: "Yozilishlar",
  vehicles: "Avtomobillar", banners: "Bannerlar", stock: "Ombor", reports: "Hisobotlar", settings: "Sozlamalar",
};
const editable = ["services", "products", "service-categories", "product-categories", "banners", "stock"];
const statusOptions = { new: ["confirmed", "cancelled"], confirmed: ["in_progress", "cancelled"], in_progress: ["completed", "cancelled"] };

export default function Admin({ useRemote, run }) {
  const [section, setSection] = useState("dashboard");
  const [edit, setEdit] = useState(null);
  const [offset, setOffset] = useState(0);
  const resource = section === "stock" ? "products" : section;
  const dashboard = useRemote("/admin/dashboard", undefined, section === "dashboard" || section === "reports");
  const business = useRemote("/business", undefined, section === "settings");
  const records = useRemote(`/admin/records/${resource}`, { offset }, !["dashboard", "reports", "settings"].includes(section));
  const serviceCategories = useRemote("/admin/records/service-categories", undefined, section === "services");
  const productCategories = useRemote("/admin/records/product-categories", undefined, resource === "products");

  function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const endpoint = resource.endsWith("-categories")
      ? `categories/${resource.split("-")[0]}` : resource;
    for (const field of ["price", "category_id", "duration", "stock"]) {
      if (field in values) values[field] = values[field] === "" ? null : Number(values[field]);
    }
    for (const field of ["image", "make"]) if (values[field] === "") values[field] = null;
    if (resource === "services") values.available = values.available === "on";
    if (resource === "banners") values.active = values.active === "on";
    run(async () => {
      await request(`/admin/${endpoint}${edit.id ? `/${edit.id}` : ""}`, edit.id ? "put" : "post", values);
      setEdit(null);
      records.reload();
    }, "O‘zgarish saqlandi");
  }

  return <section className="view">
    <div className="section-heading"><div><p className="eyebrow"><BarChart3 size={15} /> Boshqaruv paneli</p><h1>{sections[section]}</h1></div>
      {editable.includes(section) && <button className="primary" onClick={() => setEdit({})}><Plus size={17} /> Yangi yozuv</button>}</div>
    <div className="chips">{Object.entries(sections).map(([key, label]) => <button key={key} className={key === section ? "active" : ""} onClick={() => { setSection(key); setOffset(0); }}>{label}</button>)}</div>
    {["dashboard", "reports"].includes(section) && <div className="cards">
      {Object.entries(dashboard.data || {}).filter(([key]) => section !== "reports" || ["revenue", "orders", "bookings", "low_stock"].includes(key))
        .map(([key, value]) => <article className="panel metric" key={key}><span>{sections[key] || (key === "revenue" ? "Bajarilgan buyurtmalar tushumi" : "Kam qolgan mahsulotlar")}</span><strong>{key === "revenue" ? sum(value) : value}</strong></article>)}
    </div>}
    {section === "settings" && <div className="panel"><h3>Administrator ruxsatlari</h3><p>Ruxsat etilgan Telegram ID qiymatlari backend muhitidagi ADMIN_TELEGRAM_IDS orqali boshqariladi.</p>
      <h3>Aloqa ma’lumotlari</h3>{business.error && <p role="alert">{business.error}</p>}
      {business.data && <form onSubmit={(event) => {
        event.preventDefault();
        const values = Object.fromEntries(new FormData(event.currentTarget));
        run(async () => {
          await request("/admin/business", "put", Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value.trim() || null])));
          business.reload();
        }, "Aloqa ma’lumotlari saqlandi");
      }}><FormField name="phone" label="Telefon" type="tel" value={business.data.phone} required={false} />
        <FormField name="address" label="Manzil" value={business.data.address} required={false} maxLength={240} />
        <FormField name="hours" label="Ish vaqti" value={business.data.hours} required={false} maxLength={160} placeholder="09:00–18:00" />
        <p>Yozilish vaqtlarini shu yerda sozlash uchun ish vaqtini 09:00–18:00 ko‘rinishida kiriting.</p>
        <button className="primary">Saqlash</button></form>}</div>}
    {records.error && !["dashboard", "reports", "settings"].includes(section) && <p role="alert">{records.error}</p>}
    {(records.data || []).length > 0 && !["dashboard", "reports", "settings"].includes(section) && <div className="panel table-wrap"><table><thead><tr>{Object.keys(records.data[0]).map((name) => <th key={name}>{name}</th>)}<th>Amallar</th></tr></thead>
      <tbody>{records.data.map((row) => <tr key={row.id}>{Object.entries(row).map(([key, value]) => <td key={key}>{String(value ?? "—")}</td>)}<td>
        {editable.includes(section) && <button className="icon-button" aria-label="Tahrirlash" onClick={() => setEdit(row)}><Pencil size={15} /></button>}
        {!!statusOptions[row.status] && ["orders", "bookings"].includes(section) && <select value="" aria-label="Holatni yangilash" onChange={(event) => {
          const status = event.target.value;
          if (status) run(async () => { await request(`/admin/status/${section}/${row.id}`, "patch", { status }); records.reload(); }, "Holat yangilandi");
        }}><option value="">Holat</option>{statusOptions[row.status].map((status) => <option key={status} value={status}>{statuses[status]}</option>)}</select>}
      </td></tr>)}</tbody></table></div>}
    {!["dashboard", "reports", "settings"].includes(section) && !records.loading && !records.error && !records.data?.length && <p className="empty">Yozuvlar mavjud emas.</p>}
    {!["dashboard", "reports", "settings"].includes(section) && (offset > 0 || records.data?.length === 100) && <div className="actions">
      <button className="secondary" disabled={!offset} onClick={() => setOffset(offset - 100)}>Oldingi</button><button className="secondary" disabled={records.data?.length !== 100} onClick={() => setOffset(offset + 100)}>Keyingi</button>
    </div>}
    {edit && <Modal title={edit.id ? "Yozuvni tahrirlash" : "Yangi yozuv"} close={() => setEdit(null)}><form onSubmit={submit}>
      <FormField name={resource === "banners" ? "title" : "name"} label="Nomi" value={edit.name || edit.title} />
      {!resource.endsWith("-categories") && <><FormField name="description" label="Tavsif" value={edit.description} required={false} /><FormField name="image" label="Rasm havolasi" type="url" value={edit.image} required={false} /></>}
      {["products", "services"].includes(resource) && <><label>Kategoriya<select name="category_id" defaultValue={edit.category_id || ""} required><option value="">Tanlang</option>
        {(resource === "products" ? productCategories.data : serviceCategories.data)?.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <FormField name="price" label="Narx (so‘m)" type="number" min={0} value={edit.price} required={resource === "products"} /></>}
      {resource === "services" && <><FormField name="make" label="Avtomobil markasi (ixtiyoriy)" value={edit.make} required={false} /><FormField name="duration" label="Davomiyligi (daq)" type="number" value={edit.duration ?? 60} min={15} max={480} /><label className="checkbox"><input name="available" type="checkbox" defaultChecked={edit.available} /> Bron qilish mumkin</label></>}
      {resource === "products" && <><FormField name="make" label="Avtomobil markasi" value={edit.make} required={false} /><FormField name="stock" label="Ombordagi miqdor" type="number" min={0} value={edit.stock ?? 0} /></>}
      {resource === "banners" && <label className="checkbox"><input name="active" type="checkbox" defaultChecked={edit.active ?? true} /> Faol banner</label>}
      <button className="primary">Saqlash</button>
    </form></Modal>}
  </section>;
}

import { useEffect, useState } from "react";
import {
  ArrowDownRight, ArrowRight, BarChart3, CalendarDays, CarFront, CircleGauge, ClipboardList, Contact,
  House, MapPin, Moon, Package, Phone, Search, ShoppingBag, SlidersHorizontal, Sun, UserRound, Wrench, Zap,
} from "lucide-react";
import Admin from "./Admin";
import { errorText, request } from "./api";
import { Media, Modal, ProductCard, ServiceCard, Skeletons } from "./components";
import { FeedbackContext } from "./feedback";
import { sum } from "./format";
import { CustomerModal, Orders, Profile } from "./Customer";
import { navigationLabels } from "./i18n";
import { useRemote } from "./useRemote";
import "./App.css";

const pages = ["home", "services", "parts", "orders", "profile"];
const icons = [House, Wrench, Package, ClipboardList, UserRound];
const serviceIcons = [CircleGauge, Zap, Wrench, CarFront];
const urlPages = [...pages, "contact"];
const quick = [
  { title: "Diagnostika", icon: CircleGauge, text: "Motor diagnostikasi" },
  { title: "Moy almashtirish", icon: Wrench, text: "Moy almashtirish" },
  { title: "Shina xizmati", icon: CarFront, text: "Shina almashtirish" },
  { title: "Avtoelektrik", icon: Zap, text: "Avtoelektrik" },
];
const advice = [
  ["Shina bosimini muntazam tekshiring", "Shina bosimini sovuq holatda o‘lchang va ishlab chiqaruvchi ko‘rsatmalariga amal qiling."],
  ["Texnik xizmat tarixini saqlang", "Moy almashtirish, ta’mirlash va navbatdagi texnik xizmat sanalarini avtomobil profilingizga kiriting."],
];

function route() {
  const value = new URLSearchParams(location.search).get("view");
  return urlPages.includes(value) ? value : "home";
}

export default function App() {
  const webApp = window.Telegram?.WebApp;
  const [page, setPage] = useState(route);
  const [theme, setTheme] = useState(() => localStorage.getItem("magnat-theme") || webApp?.colorScheme || "dark");
  const [language, setLanguage] = useState(() => localStorage.getItem("magnat-language") || "uz");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [make, setMake] = useState("");
  const [sort, setSort] = useState("name");
  const [offset, setOffset] = useState(0);
  const [serviceCategory, setServiceCategory] = useState("");
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState(null);
  const [pending, setPending] = useState(false);
  const catalog = useRemote("/catalog", { q: search, category: category || undefined, make, sort, offset }, ["home", "services", "parts"].includes(page));
  const business = useRemote("/business", undefined, page === "home" || page === "contact");
  const fullCatalog = useRemote("/catalog", undefined, modal?.type === "booking");
  const isSession = Boolean(webApp?.initData) || import.meta.env.DEV;
  const me = useRemote("/me", undefined, isSession || page === "profile" || modal?.type === "booking");
  const isAdmin = me.data?.is_admin;
  const vehicles = useRemote("/vehicles", undefined, page === "profile" || modal?.type === "booking" || Boolean(modal?.returnToBooking));
  const saved = useRemote("/favorites", undefined, isSession && (page === "parts" || modal?.type === "favorites"));
  const cart = useRemote("/cart", undefined, isSession && (page === "parts" || ["cart", "product", "favorites"].includes(modal?.type)));

  useEffect(() => {
    webApp?.ready?.();
    webApp?.expand?.();
  }, [webApp]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.setProperty("--telegram-bg", theme === webApp?.colorScheme ? webApp?.themeParams?.bg_color || "" : "");
    localStorage.setItem("magnat-theme", theme);
    webApp?.setHeaderColor?.(theme === "light" ? "#f6f7fa" : "#0B0F19");
    webApp?.setBackgroundColor?.(theme === "light" ? "#f6f7fa" : "#0B0F19");
  }, [theme, webApp]);

  useEffect(() => {
    localStorage.setItem("magnat-language", language);
  }, [language]);

  useEffect(() => {
    function back() {
      if (modal) setModal(modal.returnToBooking || null);
      else { setPage("home"); window.scrollTo(0, 0); }
    }
    const button = webApp?.BackButton;
    if (modal || page !== "home") button?.show();
    else button?.hide();
    button?.onClick(back);
    return () => button?.offClick(back);
  }, [modal, page, webApp]);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  function go(next) {
    setPage(next);
    setSearch("");
    setQuery("");
    setOffset(0);
    if (next === "home") { setCategory(""); setMake(""); setSort("name"); }
    setServiceCategory("");
    window.scrollTo(0, 0);
  }

  function run(work, success) {
    if (pending) return;
    setPending(true);
    Promise.resolve().then(work).then(() => setToast({ text: success })).catch((error) => setToast({ text: errorText(error), error: true }))
      .finally(() => setPending(false));
  }

  function submitSearch(event) {
    event.preventDefault();
    setOffset(0);
    setSearch(query.trim());
    if (page === "home") setPage("services");
  }

  function openService(item) {
    setModal({ type: item.available ? "booking" : "service", item });
  }

  function favorite(item) {
    run(async () => {
      await request(`/favorites/${item.id}`, "put", undefined, { enabled: !saved.data?.includes(item.id) });
      saved.reload();
    }, "Sevimlilar yangilandi");
  }

  function quantity(item, amount) {
    run(async () => {
      await request(`/cart/${item.id}`, "put", { quantity: amount });
      cart.reload();
    }, "Savatcha yangilandi");
  }

  const products = (catalog.data?.products || []);
  const services = (catalog.data?.services || []).filter((item) => !serviceCategory || item.category_id === Number(serviceCategory));
  const preferredLanguage = me.data?.language || language;
  const navLabels = navigationLabels(preferredLanguage);
  const details = modal?.type === "product" ? modal.item : null;
  const cartItems = cart.data || [];
  const total = cartItems.reduce((value, item) => value + item.quantity * item.product.price, 0);

  function productCards(rows) {
    return <div className="cards">{rows.map((item) => <ProductCard key={item.id} item={item}
      favorite={saved.data?.includes(item.id) || false} onFavorite={favorite}
      onDetails={(product) => setModal({ type: "product", item: product })}
      onAdd={(product) => quantity(product, (cartItems.find((row) => row.product.id === product.id)?.quantity || 0) + 1)} />)}</div>;
  }

  return <FeedbackContext.Provider value={toast}><div className="site" aria-busy={pending}>
    <header className="topbar"><div className="shell topbar-inner">
      <button className="brand" onClick={() => go("home")} aria-label="Buxoro Avto Magnat bosh sahifa">
        <span className="brand-icon"><CarFront size={22} strokeWidth={2.5} /></span>
        <span>BUXORO <strong>AVTO MAGNAT</strong><small>AVTOMOBIL XIZMATLARI</small></span>
      </button>
      <nav className="desktop-nav" aria-label="Asosiy navigatsiya">{pages.map((key, index) => <button key={key} className={page === key ? "current" : ""} onClick={() => go(key)}>{navLabels[index]}</button>)}
        {isAdmin && <button className={page === "admin" ? "current" : ""} aria-current={page === "admin" ? "page" : undefined} aria-label="Boshqaruv paneli" onClick={() => go("admin")}>Admin</button>}
      </nav>
      <div className="top-actions"><button className="icon-button" aria-label="Mavzuni almashtirish" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}</button>
        <button className="icon-button" aria-label="Savatcha" onClick={() => setModal({ type: "cart" })}><ShoppingBag size={19} /></button></div>
    </div></header>
    <main className="shell">
      {page === "home" && <>
        <section className="hero">
          <div className="hero-copy"><p className="eyebrow"><span /> BUXORO AVTO MAGNAT</p>
            <h1>Avtomobilingiz uchun <em>ishonchli xizmat.</em></h1>
            <p>Avtoservisga yoziling, ehtiyot qismlarni toping va avtomobilingizning texnik tarixini bir joyda boshqaring.</p>
            <div className="actions"><button className="primary" onClick={() => setModal({ type: "booking" })}><CalendarDays size={18} /> Xizmatga yozilish <ArrowRight size={18} /></button>
              <button className="secondary" onClick={() => go("services")}>Xizmatlarni ko‘rish</button></div>
          </div><span className="hero-location"><MapPin size={15} /> Buxoro, O‘zbekiston</span>
        </section>
        {(business.data?.address || business.data?.phone) && <section className="section panel" aria-label="Servis manzili va telefoni"><BusinessContact data={business.data} /></section>}
        <form className="search-bar home-search" onSubmit={submitSearch}><Search size={21} /><input aria-label="Xizmat qidirish" placeholder="Xizmat nomini qidiring..." value={query} onChange={(event) => setQuery(event.target.value)} maxLength={120} /><button className="primary">Qidirish</button></form>
        <section className="section quick-section"><div className="section-heading"><div><p className="eyebrow"><span /> AVTOSERVIS</p><h2>Mashhur xizmatlar</h2></div><button className="link-button" onClick={() => go("services")}>Barcha xizmatlar <ArrowRight size={16} /></button></div>
          <div className="cards quick-cards">{quick.map(({ title, icon: Icon, text }) => <button key={title} className="quick-card" onClick={() => { go("services"); setQuery(text); setSearch(text); }}>
            <span className="service-icon"><Icon size={24} /></span><strong>{title}</strong><ArrowDownRight className="quick-arrow" size={20} /></button>)}</div>
        </section>
        {catalog.data?.banners.length > 0 && <section className="section"><div className="section-heading"><h2>Maxsus takliflar</h2></div>
          <div className="cards">{catalog.data.banners.map((item) => <article className="panel offer" key={item.id}>{item.image && <Media source={item.image} fallback="/media/service.webp" />}<h3>{item.title}</h3><p>{item.description}</p></article>)}</div></section>}
        <section className="section"><div className="section-heading"><div><p className="eyebrow"><span /> AVTOMOBIL UCHUN</p><h2>Ehtiyot qismlar</h2></div><button className="link-button" onClick={() => go("parts")}>Katalog <ArrowRight size={16} /></button></div>
          <div className="cards category-cards">{catalog.data?.product_categories.slice(0, 4).map((item) => <button className="panel" key={item.id} onClick={() => { go("parts"); setCategory(String(item.id)); }}><Package size={21} />{item.name}<ArrowRight size={17} /></button>)}</div>
          {catalog.loading && <Skeletons />}{catalog.error && <p className="empty" role="alert">{catalog.error} <button className="link-button" onClick={catalog.reload}>Qayta urinish</button></p>}</section>
        <section className="section"><div className="section-heading"><h2>Avtomobil bo‘yicha tavsiyalar</h2></div><div className="profile-grid">{advice.map(([title, text]) => <article className="panel" key={title}><h3>{title}</h3><p>{text}</p></article>)}</div></section>
      </>}
      {["services", "parts"].includes(page) && <section className="view">
        <div className="section-heading"><div><p className="eyebrow"><span /> BUXORO AVTO MAGNAT</p><h1>{page === "services" ? "Avtoservis xizmatlari" : "Ehtiyot qismlar katalogi"}</h1></div>
          {page === "parts" && <button className="secondary" onClick={() => setModal({ type: "favorites" })}>Sevimlilar</button>}</div>
        <form className="search-bar" onSubmit={submitSearch}><Search size={20} /><input aria-label="Katalogdan qidirish" value={query} onChange={(event) => setQuery(event.target.value)} maxLength={120} placeholder="Qidirish..." /><button className="primary">Qidirish</button></form>
        <div className="filters"><SlidersHorizontal size={18} />
          {page === "services" ? <select aria-label="Xizmat kategoriyasi" value={serviceCategory} onChange={(event) => setServiceCategory(event.target.value)}><option value="">Barcha kategoriyalar</option>{catalog.data?.service_categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
            : <><select aria-label="Mahsulot kategoriyasi" value={category} onChange={(event) => { setCategory(event.target.value); setOffset(0); }}><option value="">Barcha kategoriyalar</option>{catalog.data?.product_categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
              <input aria-label="Avtomobil markasi" placeholder="Avtomobil markasi" value={make} onChange={(event) => { setMake(event.target.value); setOffset(0); }} maxLength={80} />
              <select aria-label="Saralash" value={sort} onChange={(event) => { setSort(event.target.value); setOffset(0); }}><option value="name">Nomi bo‘yicha</option><option value="asc">Arzonidan boshlab</option><option value="desc">Qimmatidan boshlab</option></select></>}
        </div>
        {catalog.loading && <Skeletons />}
        {catalog.error && <p className="empty" role="alert">{catalog.error} <button className="link-button" onClick={catalog.reload}>Qayta urinish</button></p>}
        {page === "services" && <div className="cards">{services.map((item, index) => <ServiceCard key={item.id} item={item} icon={serviceIcons[index % serviceIcons.length]} onBook={openService} />)}</div>}
        {page === "parts" && productCards(products)}
        {catalog.data && !(page === "services" ? services : products).length && <p className="empty">Natija topilmadi.</p>}
        {page === "parts" && (offset > 0 || products.length === 48) && <div className="actions middle">
          <button className="secondary" disabled={!offset} onClick={() => setOffset(offset - 48)}>Oldingi</button><button className="secondary" disabled={products.length < 48} onClick={() => setOffset(offset + 48)}>Keyingi</button></div>}
      </section>}
      {page === "profile" && <Profile me={me} vehicles={vehicles} modal={setModal} run={run} language={preferredLanguage} setLanguage={setLanguage} theme={theme} setTheme={setTheme} go={go} pending={pending} />}
      {page === "orders" && <Orders />}
      {page === "admin" && isAdmin && <Admin useRemote={useRemote} run={run} />}
      {page === "contact" && <section className="view"><div className="section-heading"><h1>Aloqa</h1></div><article className="panel"><BusinessContact data={business.data} telegram /></article></section>}
    </main>
    <footer><div className="shell footer-inner"><strong>BUXORO AVTO MAGNAT</strong><button className="link-button" onClick={() => go("contact")}><MapPin size={16} /> Buxoro · Aloqa</button></div></footer>
    <nav className={isAdmin ? "bottom-nav bottom-nav-admin" : "bottom-nav"} aria-label="Mobil navigatsiya">{pages.map((key, index) => {
      const Icon = icons[index];
      return <button key={key} className={page === key ? "current" : ""} aria-current={page === key ? "page" : undefined} onClick={() => go(key)}><Icon size={20} /><span>{navLabels[index]}</span></button>;
    })}
      {isAdmin && <button className={page === "admin" ? "current" : ""} aria-current={page === "admin" ? "page" : undefined} aria-label="Boshqaruv paneli" onClick={() => go("admin")}><BarChart3 size={20} /><span>Admin</span></button>}
    </nav>
    {modal?.type === "cart" && <Modal title="Savatcha" close={() => setModal(null)}>{!isSession ? <p>Ilovani Telegram orqali oching.</p> : <>
      {cart.error && <p role="alert">{cart.error}</p>}
      {!cart.loading && !cart.error && !cartItems.length && <p>Savatcha bo‘sh.</p>}
      {cartItems.map(({ product, quantity: amount }) => <div className="cart-line" key={product.id}><div><strong>{product.name}</strong><p>{amount} × {sum(product.price)}</p></div><div className="actions">
        <button className="secondary" onClick={() => quantity(product, amount - 1)} aria-label="Kamaytirish">−</button>
        <button className="secondary" onClick={() => quantity(product, amount + 1)} disabled={amount >= product.stock} aria-label="Ko‘paytirish">+</button></div></div>)}
      {cartItems.length > 0 && <button className="primary" disabled={pending} onClick={() => run(async () => {
        await request("/orders", "post"); cart.reload(); setModal(null); go("orders");
      }, "Buyurtma qabul qilindi")}>Buyurtma berish · {sum(total)}</button>}</>}</Modal>}
    {modal?.type === "favorites" && <Modal title="Sevimli mahsulotlar" close={() => setModal(null)}>{!isSession ? <p>Ilovani Telegram orqali oching.</p> : <FavoriteList saved={saved} renderCards={productCards} />}</Modal>}
    {details && <Modal title={details.name} close={() => setModal(null)}><div className="product-detail"><Media source={details.image} fallback="/media/parts.webp" /></div><p>{details.description}</p><p>{details.make || "Universal"} · Omborda {details.stock} ta · {sum(details.price)}</p>
      <button className="primary" disabled={!details.stock} onClick={() => quantity(details, (cartItems.find((item) => item.product.id === details.id)?.quantity || 0) + 1)}>Savatchaga qo‘shish</button></Modal>}
    {modal && ["booking", "vehicle", "maintenance", "service"].includes(modal.type) && <CustomerModal key={modal.type} modal={modal}
      close={() => setModal(modal.returnToBooking || null)} run={run} openModal={setModal} pending={pending}
      vehicles={vehicles} source={fullCatalog} me={me.data} go={go} />}
    {toast && <div className={`toast ${toast.error ? "toast-error" : ""}`} role={toast.error ? "alert" : "status"}>{toast.text}</div>}
  </div></FeedbackContext.Provider>;
}

function BusinessContact({ data, telegram }) {
  const { address, hours, phone } = data || {};
  return <>
    <p>{address || "Buxoro, O‘zbekiston"}</p>
    {hours && <p>{hours}</p>}
    {phone && <p>{phone}</p>}
    <div className="actions">
      {address && <a className="secondary" href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`} target="_blank" rel="noreferrer"><MapPin size={17} /> Xaritada ochish</a>}
      {phone && <a className="secondary" href={`tel:${phone}`}><Phone size={17} /> Qo‘ng‘iroq qilish</a>}
      {telegram && <a className="primary" href="https://t.me/BuxaraAvtoMagnatBot"><Contact size={18} /> Telegram orqali bog‘lanish</a>}
    </div>
  </>;
}

function FavoriteList({ saved, renderCards }) {
  const favorites = useRemote("/favorites/products");
  if (saved.error || favorites.error) return <p role="alert">{saved.error || favorites.error}</p>;
  if (favorites.loading) return <p>Yuklanmoqda…</p>;
  const products = favorites.data.filter((item) => saved.data?.includes(item.id));
  return products.length ? renderCards(products) : <p>Sevimlilar mavjud emas.</p>;
}

import { useContext, useEffect, useRef } from "react";
import { ArrowUpRight, Clock3, Heart, Package, ShoppingBag, Wrench, X } from "lucide-react";

import { FeedbackContext } from "./feedback";
import { sum } from "./format";

export function Modal({ title, children, close }) {
  const dialog = useRef(null);
  const feedback = useContext(FeedbackContext);
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  return <dialog ref={dialog} onCancel={(event) => { event.preventDefault(); close(); }} aria-labelledby="modal-title">
    <div className="modal-top"><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label="Yopish" onClick={close}><X /></button></div>
    {feedback && <p className={`dialog-feedback ${feedback.error ? "dialog-feedback-error" : ""}`}
      role={feedback.error ? "alert" : "status"}>{feedback.text}</p>}
    {children}
  </dialog>;
}

export function Skeletons() {
  return <div className="cards" aria-label="Yuklanmoqda" role="status">
    {[0, 1, 2, 3].map((index) => <div className="skeleton" key={index} />)}
  </div>;
}

export function Media({ source, fallback, label }) {
  return <img alt={label || ""} loading="lazy" src={source || fallback}
    onError={source ? (event) => { if (event.currentTarget.getAttribute("src") !== fallback) event.currentTarget.src = fallback; } : undefined} />;
}

export function ServiceCard({ item, icon: Icon = Wrench, onBook }) {
  return <article className="service-card">
    <div className="service-top"><div className="service-visual"><Media source={item.image} fallback="/media/service.webp" /><span className="service-icon"><Icon size={18} /></span></div>
      <button className="card-arrow" aria-label={item.name} onClick={() => onBook(item)}><ArrowUpRight size={18} /></button>
    </div>
    <h3>{item.name}</h3><p>{item.description}</p>
    <div className="card-meta"><span>{sum(item.price)}</span><span><Clock3 size={14} /> {item.available ? `${item.duration} daq` : "Bron yopiq"}</span></div>
  </article>;
}

export function ProductCard({ item, favorite, onFavorite, onAdd, onDetails }) {
  return <article className="product-card">
    <div className="product-media"><button className="product-image" onClick={() => onDetails(item)} aria-label={item.name}>
      <Media source={item.image} fallback="/media/parts.webp" />
    </button><button className={`icon-button favorite ${favorite ? "selected" : ""}`} aria-label="Sevimlilar" aria-pressed={favorite} onClick={() => onFavorite(item)}><Heart size={18} fill={favorite ? "currentColor" : "none"} /></button></div>
    <div className="product-body"><button className="text-button" onClick={() => onDetails(item)}>{item.name}</button>
      <p><Package size={14} /> {item.stock > 0 ? `Omborda ${item.stock} ta` : "Tugagan"}{item.make ? ` · ${item.make}` : ""}</p>
      <div className="card-meta"><strong>{sum(item.price)}</strong><button className="icon-button" disabled={item.stock < 1} aria-label="Savatchaga qo‘shish" onClick={() => onAdd(item)}><ShoppingBag size={18} /></button></div>
    </div>
  </article>;
}

export function FormField({ name, label, type = "text", value, required = true, ...props }) {
  return <label>{label}<input name={name} type={type} defaultValue={value ?? ""} required={required} {...props} /></label>;
}

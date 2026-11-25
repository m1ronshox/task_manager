const navigation = {
  uz: ["Bosh sahifa", "Xizmatlar", "Ehtiyot qismlar", "Buyurtmalar", "Profil"],
  ru: ["Главная", "Услуги", "Запчасти", "Заказы", "Профиль"],
  en: ["Home", "Services", "Parts", "Orders", "Profile"],
};

export function navigationLabels(language) {
  return navigation[language] || navigation.uz;
}

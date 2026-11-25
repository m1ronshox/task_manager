export const sum = (amount) => amount == null ? "Narx belgilanmagan"
  : `${new Intl.NumberFormat("uz-UZ").format(amount)} so‘m`;
export const statuses = {
  new: "Yangi", confirmed: "Tasdiqlangan", in_progress: "Jarayonda",
  completed: "Bajarilgan", cancelled: "Bekor qilingan",
};

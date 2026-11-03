const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  summary: () => request("/analytics/summary"),
  products: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) params.set(key, value);
    });
    return request(`/products${params.size ? `?${params}` : ""}`);
  },
  product: (id) => request(`/products/${id}`),
  createProduct: (data) => request("/products", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  }),
  updateProduct: (id, data) => request(`/products/${id}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  }),
  deleteProduct: (id) => request(`/products/${id}`, { method: "DELETE" }),
  recommendations: (params) => request(`/recommendations?${new URLSearchParams(params)}`),
  importFile: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/products/import", { method: "POST", body: form });
  },
};

export const money = (amount) => amount == null
  ? "—"
  : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);

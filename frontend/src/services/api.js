import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body.code !== 0) {
      return Promise.reject(new Error(body.message || "Request failed"));
    }
    return body.data;
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || "Network error";
    return Promise.reject(new Error(msg));
  }
);

export default api;

export const caseAPI = {
  list: (params) => api.get("/cases", { params }),
  get: (id) => api.get(`/cases/${id}`),
  create: (data) => api.post("/cases", data),
  update: (id, data) => api.put(`/cases/${id}`, data),
  remove: (id) => api.delete(`/cases/${id}`),
  extract: (data) => api.post("/cases/extract", data),
};

export const customerAPI = {
  list: (params) => api.get("/customers", { params }),
  get: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post("/customers", data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  remove: (id) => api.delete(`/customers/${id}`),
};

export const visitAPI = {
  listPlans: (params) => api.get("/visits/plans", { params }),
  getPlan: (id) => api.get(`/visits/plans/${id}`),
  createPlan: (data) => api.post("/visits/plans", data),
  updatePlan: (id, data) => api.put(`/visits/plans/${id}`, data),
  removePlan: (id) => api.delete(`/visits/plans/${id}`),
  listRecords: (params) => api.get("/visits/records", { params }),
  getRecord: (id) => api.get(`/visits/records/${id}`),
  createRecord: (data) => api.post("/visits/records", data),
  updateRecord: (id, data) => api.put(`/visits/records/${id}`, data),
};

export const todoAPI = {
  list: (params) => api.get("/todos", { params }),
  get: (id) => api.get(`/todos/${id}`),
  create: (data) => api.post("/todos", data),
  update: (id, data) => api.put(`/todos/${id}`, data),
  remove: (id) => api.delete(`/todos/${id}`),
};

export const searchAPI = {
  customers: (data) => api.post("/search/customers", data),
  cases: (data) => api.post("/search/cases", data),
};

export const productAPI = {
  list: (params) => api.get("/products", { params }),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post("/products", data),
  update: (id, data) => api.put(`/products/${id}`, data),
  remove: (id) => api.delete(`/products/${id}`),
};

export const businessAPI = {
  summary: () => api.get("/business/summary"),
  export: () => api.get("/business/export"),
  engagements: {
    list: (params) => api.get("/engagements", { params }),
    get: (id) => api.get(`/engagements/${id}`),
    create: (data) => api.post("/engagements", data),
    update: (id, data) => api.put(`/engagements/${id}`, data),
    remove: (id) => api.delete(`/engagements/${id}`),
  },
  artifacts: {
    list: (params) => api.get("/artifacts", { params }),
    get: (id) => api.get(`/artifacts/${id}`),
    create: (data) => api.post("/artifacts", data),
    update: (id, data) => api.put(`/artifacts/${id}`, data),
    remove: (id) => api.delete(`/artifacts/${id}`),
  },
};

export const agentAPI = {
  capabilities: () => api.get("/agent/capabilities"),
  runAction: (data) => api.post("/agent/actions", data),
};

export const aiAPI = {
  meddic: (data) => api.post("/ai/meddic", data),
  opening: (data) => api.post("/ai/opening", data),
  intel: (data) => api.post("/ai/intel", data),
};

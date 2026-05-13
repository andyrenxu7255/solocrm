import { create } from "zustand";

const useAppStore = create((set) => ({
  customers: [],
  cases: [],
  visits: [],
  todos: [],
  loading: false,
  error: null,

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

export default useAppStore;

import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Marketplace from "./pages/Marketplace";
import Recommendations from "./pages/Recommendations";
import ListingForm from "./pages/ListingForm";

export default function App() {
  return <Routes><Route element={<Layout />}><Route index element={<Dashboard />} /><Route path="marketplace" element={<Marketplace />} /><Route path="recommendations" element={<Recommendations />} /><Route path="add-listing" element={<ListingForm />} /><Route path="*" element={<Dashboard />} /></Route></Routes>;
}

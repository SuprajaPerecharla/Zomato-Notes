import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import NoteDetail from "./components/NoteDetail";
import NoteEditor from "./components/NoteEditor";
import SearchPage from "./components/SearchPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="notes/new" element={<NoteEditor />} />
        <Route path="notes/:id" element={<NoteDetail />} />
        <Route path="notes/:id/edit" element={<NoteEditor />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

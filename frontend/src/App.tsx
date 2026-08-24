import { NavLink, Route, Routes, useMatch } from "react-router-dom";

import AdminPage from "./routes/AdminPage";
import BookPage from "./routes/BookPage";
import LibraryPage from "./routes/LibraryPage";
import ReaderPage from "./routes/ReaderPage";
import TagsPage from "./routes/TagsPage";
import { useTheme } from "./theme/useTheme";
import styles from "./App.module.css";

export default function App() {
  const { theme, toggle } = useTheme();
  const isReader = !!useMatch("/read/:id");
  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <NavLink to="/" className={styles.brand}>
          labooke
        </NavLink>
        <nav className={styles.nav}>
          <NavLink to="/" end>
            Library
          </NavLink>
          <NavLink to="/tags">Tags</NavLink>
          <NavLink to="/admin">Admin</NavLink>
        </nav>
        <button
          type="button"
          className={styles.themeToggle}
          onClick={toggle}
          aria-label="Toggle color theme"
        >
          {theme === "light" ? "Dark mode" : theme === "dark" ? "Night mode" : "Light mode"}
        </button>
      </header>
      <main className={isReader ? styles.mainReader : styles.main}>
        <Routes>
          <Route path="/" element={<LibraryPage />} />
          <Route path="/book/:id" element={<BookPage />} />
          <Route path="/read/:id" element={<ReaderPage />} />
          <Route path="/tags" element={<TagsPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}

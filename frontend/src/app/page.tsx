import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <p className={styles.eyebrow}>LeadFlow AI</p>
        <h1>Keep every lead moving.</h1>
        <p className={styles.description}>A focused workspace for capturing and following up with your business leads.</p>
        <div className={styles.ctas}>
          <Link className={styles.primary} href="/login">Log in</Link>
          <Link className={styles.secondary} href="/signup">Create account</Link>
        </div>
      </main>
    </div>
  );
}

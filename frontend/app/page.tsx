import Navbar from "@/components/marketing/Navbar";
import Hero from "@/components/marketing/Hero";
import ProblemSection from "@/components/marketing/ProblemSection";
import WorkflowSection from "@/components/marketing/WorkflowSection";
import CapabilitiesSection from "@/components/marketing/CapabilitiesSection";
import ClosingCTA from "@/components/marketing/ClosingCTA";
import Footer from "@/components/marketing/Footer";

export default function Home() {
  return (
    <div className="min-h-screen font-sans selection:bg-[var(--color-primary-gold)] selection:text-[var(--color-surface)]">
      <Navbar />
      
      <main className="flex flex-col items-center w-full">
        <Hero />
        <ProblemSection />
        <WorkflowSection />
        <CapabilitiesSection />
        <ClosingCTA />
      </main>

      <Footer />
    </div>
  );
}

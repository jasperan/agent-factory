import { Wrench } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-12 px-4 bg-rivet-gray border-t border-gray-800">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <Wrench className="w-6 h-6 text-rivet-orange" />
            <span className="text-xl font-bold text-white">Rivet</span>
          </div>

          <div className="flex gap-8 text-gray-400">
            <a href="#" className="hover:text-white transition">Privacy</a>
            <a href="#" className="hover:text-white transition">Terms</a>
            <a href="mailto:support@rivet.app" className="hover:text-white transition">Support</a>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          © 2025 Rivet. Built for the field.
        </div>
      </div>
    </footer>
  );
}

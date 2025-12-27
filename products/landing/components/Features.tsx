import { MessageSquare, Upload, Search, Shield, Zap, Database } from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "Voice-First",
    description: "Speak naturally to create work orders, query equipment, and get troubleshooting help."
  },
  {
    icon: Upload,
    title: "Upload Prints",
    description: "Upload electrical prints and schematics. Ask questions about any circuit or component."
  },
  {
    icon: Search,
    title: "Smart Search",
    description: "AI understands equipment context. Ask about PowerFlex faults and get manual excerpts."
  },
  {
    icon: Database,
    title: "Manual Library",
    description: "Build your searchable library of OEM manuals. Get answers with page citations."
  },
  {
    icon: Shield,
    title: "Safety First",
    description: "Every response includes relevant safety warnings. LOTO reminders built in."
  },
  {
    icon: Zap,
    title: "Instant Answers",
    description: "No more digging through binders. Get the right info in seconds."
  }
];

export default function Features() {
  return (
    <section className="py-20 px-4 bg-rivet-gray">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-4 text-white">
          Built for <span className="text-rivet-orange">Field Technicians</span>
        </h2>
        <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
          Everything you need to troubleshoot faster and document better.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <div key={i} className="bg-rivet-dark p-6 rounded-xl">
              <feature.icon className="w-10 h-10 text-rivet-orange mb-4" />
              <h3 className="text-xl font-semibold mb-2 text-white">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

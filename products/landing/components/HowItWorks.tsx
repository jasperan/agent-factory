export default function HowItWorks() {
  const steps = [
    {
      number: "1",
      title: "Open Telegram",
      description: "Search @RivetCMMS_bot in Telegram"
    },
    {
      number: "2",
      title: "Send Voice Message",
      description: "Say 'The main pump is making noise'"
    },
    {
      number: "3",
      title: "Work Order Created",
      description: "Automatically logged with equipment details"
    }
  ];

  return (
    <section id="how-it-works" className="py-20 px-4 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="bg-blue-600 text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                {step.number}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {step.title}
              </h3>
              <p className="text-gray-600">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

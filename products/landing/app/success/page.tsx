import Link from "next/link";

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-2xl mx-auto text-center">
        <div className="text-6xl mb-6">🎉</div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Rivet!
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Your account is ready. Here's how to get started:
        </p>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <ol className="text-left space-y-4">
            <li className="flex items-start">
              <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                1
              </span>
              <div>
                <strong className="block text-lg mb-1">Open Telegram on your phone</strong>
                <p className="text-gray-600">Available on iOS and Android</p>
              </div>
            </li>
            <li className="flex items-start">
              <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                2
              </span>
              <div>
                <strong className="block text-lg mb-1">Search for <code className="bg-gray-100 px-2 py-1 rounded">@RivetCMMS_bot</code></strong>
                <p className="text-gray-600">Find the official Rivet bot</p>
              </div>
            </li>
            <li className="flex items-start">
              <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                3
              </span>
              <div>
                <strong className="block text-lg mb-1">Tap <strong>Start</strong></strong>
                <p className="text-gray-600">Initialize your account connection</p>
              </div>
            </li>
            <li className="flex items-start">
              <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                4
              </span>
              <div>
                <strong className="block text-lg mb-1">Send your first voice message!</strong>
                <p className="text-gray-600">Try: "The main pump is making noise"</p>
              </div>
            </li>
          </ol>
        </div>

        <a
          href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/RivetCMMS_bot"}
          className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition mb-4"
        >
          Open Telegram Bot →
        </a>

        <p className="text-gray-600">
          Need help?{" "}
          <a href="mailto:support@rivet.com" className="text-blue-600 hover:underline">
            Contact support
          </a>
        </p>

        <div className="mt-8">
          <Link href="/" className="text-blue-600 hover:underline">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}

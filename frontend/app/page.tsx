export default function Page() {
  return (
    <main className="space-y-4">
      <p className="text-lg">
        Welcome. Start by connecting your email account.
      </p>
      <a
        href="/connect"
        className="inline-flex items-center rounded-md bg-black px-3 py-2 text-white hover:bg-gray-800"
      >
        Connect Nylas
      </a>
    </main>
  );
}

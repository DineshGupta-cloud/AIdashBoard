export default function Search({ query, setQuery, search, results }) {
  return (
    <div className="rounded-2xl bg-slate-900 p-5 space-y-4">
      <h2 className="text-xl font-bold">Strategy Search</h2>
      <div className="flex gap-2">
        <input value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1 bg-slate-800 px-3 py-2 rounded-xl" placeholder="iron / bullish / hedge" />
        <button onClick={search} className="bg-blue-600 px-4 py-2 rounded-xl">Search</button>
      </div>
      {results.map((item) => (
        <div key={item.id} className="bg-slate-800 p-3 rounded-xl">
          <div className="font-semibold">{item.name}</div>
          <div className="text-sm text-slate-400">{item.marketView}</div>
        </div>
      ))}
    </div>
  );
}
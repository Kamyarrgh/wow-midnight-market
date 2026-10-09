import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  RefreshCw,
  Database,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [materials, setMaterials] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/api/materials`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setMaterials(data);
      if (data.length > 0 && !selectedItem) {
        setSelectedItem(data[0]);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError('خطا در برقراری ارتباط با API سرور.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchHistory = async (itemId) => {
    try {
      const res = await fetch(`${API_BASE}/api/materials/${itemId}/history?region=eu`);
      if (!res.ok) {
        setHistory([]);
        return;
      }
      const data = await res.json();
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('History fetch error:', err);
      setHistory([]);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedItem) {
      fetchHistory(selectedItem.item_id);
    }
  }, [selectedItem]);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await fetchData();
  };

  const formatGold = (copper) => {
    if (!copper && copper !== 0) return '0g';
    const gold = Math.floor(copper / 10000);
    return `${gold.toLocaleString()}g`;
  };

  const formatUpdated = (iso) => {
    if (!iso) return '--';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '--';
    return d.toLocaleString('fa-IR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center space-x-3 rtl:space-x-reverse">
          <Database className="w-6 h-6 text-amber-500" />
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
            WoW Midnight Market Tracker
          </h1>
          <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
            Local v1.0
          </span>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 rtl:space-x-reverse bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 text-sm transition"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-amber-400' : ''}`} />
          <span>بروزرسانی داده‌ها</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-x-6 rtl:space-x-reverse flex flex-col lg:flex-row gap-6">
        {/* Left Side: Materials List */}
        <div className="w-full lg:w-1/3 bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4 px-2">
            متریال‌های ردیابی شده
          </h2>
          {loading ? (
            <div className="p-8 text-center text-slate-500 text-sm">در حال بارگذاری متریال‌ها...</div>
          ) : error ? (
            <div className="p-4 bg-red-950/30 border border-red-900 text-red-400 text-xs rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : materials.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">آیتمی یافت نشد.</div>
          ) : (
            <div className="space-y-2 overflow-y-auto max-h-[70vh] pr-1">
              {materials.map((mat) => {
                const isSelected = selectedItem?.item_id === mat.item_id;
                return (
                  <div
                    key={mat.item_id}
                    onClick={() => setSelectedItem(mat)}
                    className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-amber-950/20 border-amber-600/50 shadow-sm'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-sm text-slate-200">{mat.name}</div>
                      <div className="text-xs text-slate-500">ID: {mat.item_id}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-amber-400">
                        {formatGold(mat.current_price_copper)}
                      </div>
                      <div className="text-xs text-slate-400">
                        {mat.quantity != null ? `موجودی: ${mat.quantity.toLocaleString()}` : 'موجودی: --'}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side: Material Detail & Chart */}
        <div className="w-full lg:w-2/3 space-y-6">
          {selectedItem ? (
            <>
              {/* Stat Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-500 font-medium uppercase">قیمت فعلی (Min Buyout)</div>
                  <div className="text-2xl font-bold text-amber-400 mt-1">
                    {formatGold(selectedItem.current_price_copper)}
                  </div>
                </div>

                <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-500 font-medium uppercase">حجم عرضه (Quantity)</div>
                  <div className="text-2xl font-bold text-slate-200 mt-1">
                    {selectedItem.quantity?.toLocaleString() || '--'}
                  </div>
                </div>

                <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-500 font-medium uppercase">آخرین بروزرسانی</div>
                  <div className="text-2xl font-bold text-slate-200 mt-1">
                    {formatUpdated(selectedItem.last_updated)}
                  </div>
                </div>
              </div>

              {/* Chart */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-slate-300">
                    روند قیمت ۴۸ ساعت اخیر: {selectedItem.name}
                  </h3>
                </div>
                <div className="h-72 w-full">
                  {history.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={history}>
                        <defs>
                          <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis
                          dataKey="timestamp"
                          stroke="#64748b"
                          tick={{ fontSize: 11 }}
                          tickFormatter={(time) => {
                            try {
                              const d = new Date(time);
                              return `${d.getHours()}:00`;
                            } catch {
                              return time;
                            }
                          }}
                        />
                        <YAxis
                          stroke="#64748b"
                          tick={{ fontSize: 11 }}
                          tickFormatter={(val) => `${Math.floor(val / 10000)}g`}
                        />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                          labelStyle={{ color: '#94a3b8' }}
                          formatter={(value) => [`${formatGold(value)}`, 'قیمت']}
                        />
                        <Area
                          type="monotone"
                          dataKey="price_gold"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          fillOpacity={1}
                          fill="url(#colorPrice)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-slate-600 text-sm">
                      داده‌های تاریخی برای این متریال ثبت نشده است.
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-600 text-sm border border-slate-800 rounded-xl">
              برای مشاهده نمودار و جزییات، یک آیتم را از لیست انتخاب کنید.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

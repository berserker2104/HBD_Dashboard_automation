import React, { useState, useEffect } from "react";
import { Card, Typography, Input, Button } from "@material-tailwind/react";
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  MapPinIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import api from "../../utils/Api";

// ─── Summary stat mini-card ───────────────────────────────────────────────────
const SummaryCard = ({ label, value, colorClass, Icon }) => (
  <Card className={`p-5 bg-white border-l-4 ${colorClass} shadow-sm rounded-xl flex items-center gap-4`}>
    <div className={`p-3 rounded-lg ${colorClass.replace("border-", "bg-").replace("-500", "-50")}`}>
      <Icon className={`h-6 w-6 ${colorClass.replace("border-", "text-")}`} />
    </div>
    <div>
      <Typography variant="small" className="text-slate-500 font-semibold uppercase tracking-wider">
        {label}
      </Typography>
      <Typography variant="h3" className="font-bold text-slate-800">
        {value ?? "—"}
      </Typography>
    </div>
  </Card>
);

// ─── Status badge ────────────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const map = {
    completed:  "bg-emerald-50 text-emerald-700 border border-emerald-200",
    processing: "bg-blue-50    text-blue-700    border border-blue-200",
    failed:     "bg-rose-50    text-rose-700    border border-rose-200",
    pending:    "bg-slate-100  text-slate-600   border border-slate-200",
  };
  return (
    <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${map[status] || map.pending}`}>
      {status?.toUpperCase()}
    </span>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────
const MasterDataUploader = () => {
  const [file, setFile]               = useState(null);
  const [sourceName, setSourceName]   = useState("");
  const [loading, setLoading]         = useState(false);
  const [summary, setSummary]         = useState(null);
  const [history, setHistory]         = useState([]);
  const [histLoading, setHistLoading] = useState(true);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    setHistLoading(true);
    try {
      const res = await api.get("/listing-upload/history");
      setHistory(res.data || []);
    } catch (err) {
      console.error("History fetch failed:", err);
    } finally {
      setHistLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a file first.");

    const formData = new FormData();
    formData.append("file", file);
    if (sourceName.trim()) formData.append("source_name", sourceName.trim());

    try {
      setLoading(true);
      setSummary(null);
      const res = await api.post("/listing-upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSummary(res.data);
      setFile(null);
      setSourceName("");
      fetchHistory();
    } catch (err) {
      console.error("Upload error:", err);
      const msg = err.response?.data?.details || err.response?.data?.error || "Upload failed.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const summaryCards = summary
    ? [
        { label: "Total Rows",          value: summary.total_rows,              colorClass: "border-blue-500",   Icon: DocumentTextIcon     },
        { label: "Inserted",             value: summary.inserted_rows,           colorClass: "border-emerald-500",Icon: CheckCircleIcon       },
        { label: "Updated",              value: summary.updated_rows,            colorClass: "border-indigo-500", Icon: ArrowPathIcon         },
        { label: "Duplicates Skipped",   value: summary.duplicate_rows,          colorClass: "border-slate-400",  Icon: XCircleIcon           },
        { label: "Location Matched",     value: summary.matched_location_rows,   colorClass: "border-green-500",  Icon: MapPinIcon            },
        { label: "Location Unmatched",   value: summary.unmatched_location_rows, colorClass: "border-orange-500", Icon: ExclamationCircleIcon },
      ]
    : [];

  const historyColumns = [
    { key: "file_name",               label: "File Name"          },
    { key: "source_name",             label: "Source"             },
    { key: "file_type",               label: "Type"               },
    { key: "upload_status",           label: "Status"             },
    { key: "total_rows",              label: "Total"              },
    { key: "inserted_rows",           label: "Inserted"           },
    { key: "updated_rows",            label: "Updated"            },
    { key: "duplicate_rows",          label: "Duplicates"         },
    { key: "matched_location_rows",   label: "Loc. Matched"       },
    { key: "unmatched_location_rows", label: "Loc. Unmatched"     },
    { key: "created_at",              label: "Uploaded"           },
    { key: "error_message",           label: "Error"              },
  ];

  return (
    <div className="p-4 md:p-8 bg-slate-50 min-h-screen flex flex-col gap-8">

      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-blue-50 rounded-xl">
          <ArrowUpTrayIcon className="h-7 w-7 text-blue-600" />
        </div>
        <div>
          <Typography variant="h4" color="blue-gray" className="font-bold leading-tight">
            Listing Data Upload
          </Typography>
          <Typography variant="small" className="text-slate-500">
            Upload PDF, Excel, or CSV — data is extracted and imported directly into master table.
          </Typography>
        </div>
      </div>

      {/* ── Upload form ── */}
      <Card className="p-6 border border-slate-100 shadow-sm bg-white rounded-xl">
        <Typography variant="h6" color="blue-gray" className="font-bold mb-4">
          Upload File
        </Typography>
        <form onSubmit={handleUpload} className="flex flex-col md:flex-row gap-4 items-end">

          {/* Source name */}
          <div className="w-full md:w-56">
            <Input
              label="Source Name (optional)"
              value={sourceName}
              onChange={e => setSourceName(e.target.value)}
              color="blue"
            />
          </div>

          {/* File picker */}
          <div className="relative w-full md:flex-1 border-2 border-dashed border-slate-300 rounded-lg
                          px-4 py-3 hover:bg-slate-50 transition cursor-pointer flex items-center justify-center min-h-[44px]">
            <input
              type="file"
              accept=".csv,.xls,.xlsx,.pdf"
              onChange={e => setFile(e.target.files[0])}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              required
            />
            <span className={`text-sm font-medium ${file ? "text-blue-600" : "text-slate-500"}`}>
              {file ? file.name : "Click to select file  (PDF / CSV / Excel)"}
            </span>
          </div>

          {/* Submit */}
          <div className="w-full md:w-48">
            <Button
              type="submit"
              color="blue"
              fullWidth
              disabled={loading || !file}
              className="flex items-center justify-center gap-2 h-10"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Processing…
                </>
              ) : (
                <><ArrowUpTrayIcon className="h-4 w-4" /> Upload & Import</>
              )}
            </Button>
          </div>
        </form>
      </Card>

      {/* ── Summary cards ── */}
      {summary && (
        <div>
          <Typography variant="h6" color="blue-gray" className="font-bold mb-3">
            Import Summary
          </Typography>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {summaryCards.map((c, i) => <SummaryCard key={i} {...c} />)}
          </div>
        </div>
      )}

      {/* ── Upload history ── */}
      <Card className="border border-slate-100 shadow-sm bg-white rounded-xl overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DocumentTextIcon className="h-5 w-5 text-slate-500" />
            <Typography variant="h6" color="blue-gray" className="font-bold">
              Upload History
            </Typography>
          </div>
          <button
            onClick={fetchHistory}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-blue-500 transition"
          >
            <ArrowPathIcon className={`h-4 w-4 ${histLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-max table-auto text-left">
            <thead>
              <tr>
                {historyColumns.map(c => (
                  <th
                    key={c.key}
                    className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider
                               bg-slate-50 border-b border-slate-200 whitespace-nowrap"
                  >
                    {c.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {histLoading ? (
                <tr>
                  <td colSpan={historyColumns.length} className="py-12 text-center text-slate-400">
                    Loading history…
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={historyColumns.length} className="py-12 text-center text-slate-400">
                    No uploads yet.
                  </td>
                </tr>
              ) : (
                history.map(row => (
                  <tr key={row.id} className="hover:bg-slate-50 transition-colors border-b border-slate-50">
                    {historyColumns.map(col => (
                      <td key={col.key} className="px-4 py-3 text-sm text-slate-700 whitespace-nowrap">
                        {col.key === "upload_status" ? (
                          <StatusBadge status={row[col.key]} />
                        ) : col.key === "error_message" ? (
                          row[col.key] ? (
                            <span className="text-rose-600 text-xs max-w-[200px] block truncate" title={row[col.key]}>
                              {row[col.key]}
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )
                        ) : col.key === "created_at" ? (
                          row[col.key]
                            ? new Date(row[col.key]).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })
                            : "—"
                        ) : (
                          row[col.key] ?? "—"
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default MasterDataUploader;
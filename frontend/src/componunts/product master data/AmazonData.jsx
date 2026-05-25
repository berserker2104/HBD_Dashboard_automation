import React, { useEffect, useState, useCallback } from "react";
import api from "@/utils/Api";
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  Typography,
  Input,
  Spinner,
} from "@material-tailwind/react";
import {
  ChevronUpDownIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  LinkIcon,
  StarIcon,
} from "@heroicons/react/24/solid";
import { FireIcon } from "@heroicons/react/24/outline";
import * as XLSX from "xlsx/dist/xlsx.full.min.js";

const COLUMNS = [
  { key: "asin",             label: "ASIN",            width: "w-[90px]"  },
  { key: "title",            label: "Product Name",    width: "w-[300px]" },
  { key: "categoryName",     label: "Category",        width: "w-[160px]" },
  { key: "price",            label: "Price (₹)",       width: "w-[80px]"  },
  { key: "listPrice",        label: "MRP (₹)",         width: "w-[80px]"  },
  { key: "stars",            label: "Stars",           width: "w-[80px]"  },
  { key: "reviews",          label: "Reviews",         width: "w-[80px]"  },
  { key: "isBestSeller",     label: "Best Seller",     width: "w-[80px]"  },
  { key: "boughtInLastMonth",label: "Bought/Month",    width: "w-[90px]"  },
  { key: "productUrl",       label: "Link",            width: "w-[60px]"  },
];

const StarRating = ({ stars }) => {
  if (!stars) return <span className="text-gray-400">—</span>;
  return (
    <span className="flex items-center gap-1 text-amber-500 font-semibold text-sm">
      <StarIcon className="h-3.5 w-3.5" />
      {Number(stars).toFixed(1)}
    </span>
  );
};

const AmazonData = () => {
  const [loading, setLoading]           = useState(true);
  const [pageData, setPageData]         = useState([]);
  const [currentPage, setCurrentPage]   = useState(1);
  const [totalPages, setTotalPages]     = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [error, setError]               = useState(null);
  const [search, setSearch]             = useState("");
  const [categorySearch, setCategorySearch] = useState("");
  const limit = 50;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get("/amazon/fetch-data", {
        params: { page: currentPage, limit, search, category: categorySearch },
      });
      const result = response.data;
      setPageData(result.data || []);
      setTotalPages(result.total_pages || 1);
      setTotalRecords(result.total_count || 0);
    } catch (err) {
      console.error("Fetch Error:", err);
      setError("Failed to fetch Amazon data.");
    } finally {
      setLoading(false);
    }
  }, [currentPage, search, categorySearch]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const exportToExcel = () => {
    if (!pageData.length) return;
    const ws = XLSX.utils.json_to_sheet(pageData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Amazon_Data");
    XLSX.writeFile(wb, `Amazon_Products_Page_${currentPage}.xlsx`);
  };

  const renderCell = (col, row) => {
    const val = row[col.key];
    if (col.key === "productUrl") {
      return val ? (
        <a href={val} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-700">
          <LinkIcon className="h-4 w-4" />
        </a>
      ) : "—";
    }
    if (col.key === "stars") return <StarRating stars={val} />;
    if (col.key === "isBestSeller") {
      return val ? (
        <span className="flex items-center gap-1 text-xs font-semibold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">
          <FireIcon className="h-3 w-3" /> Best
        </span>
      ) : "—";
    }
    if (col.key === "price" || col.key === "listPrice") {
      return val ? `₹${Number(val).toLocaleString("en-IN")}` : "—";
    }
    if (col.key === "reviews" || col.key === "boughtInLastMonth") {
      return val ? Number(val).toLocaleString("en-IN") : "—";
    }
    if (col.key === "title") {
      return (
        <span className="block max-w-[280px] truncate" title={val}>{val || "—"}</span>
      );
    }
    return val || "—";
  };

  return (
    <div className="min-h-screen mt-8 mb-12 px-4 rounded bg-white text-black">

      {/* Header */}
      <div className="flex flex-wrap justify-between items-end mb-6 gap-4">
        <div>
          <Typography variant="h4" className="font-bold text-blue-gray-900">
            Amazon Product Master
          </Typography>
          <Typography variant="small" className="font-medium text-gray-500">
            {error ? (
              <span className="text-red-500 font-bold">{error}</span>
            ) : (
              `${totalRecords.toLocaleString("en-IN")} total products`
            )}
          </Typography>
        </div>
        <div className="flex gap-2">
          <Button variant="gradient" color="green" size="sm" className="flex items-center gap-2" onClick={exportToExcel}>
            <ArrowDownTrayIcon className="h-4 w-4" /> Export Page
          </Button>
          <Button variant="outlined" size="sm" className="flex items-center gap-2" onClick={fetchData} disabled={loading}>
            <ArrowPathIcon className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>
      </div>

      <Card className="h-full w-full border border-blue-gray-100 overflow-hidden">
        {/* Filters + Pagination */}
        <CardHeader floated={false} shadow={false} className="rounded-none p-4 bg-blue-gray-50/50">
          <div className="flex flex-wrap items-center justify-between gap-y-4">
            <div className="flex flex-wrap gap-3">
              <div className="w-72">
                <Input
                  label="Search Product Name"
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
                />
              </div>
              <div className="w-48">
                <Input
                  label="Filter by Category"
                  value={categorySearch}
                  onChange={(e) => { setCategorySearch(e.target.value); setCurrentPage(1); }}
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Typography variant="small" className="font-bold text-blue-gray-700 whitespace-nowrap">
                Page {currentPage} of {totalPages}
              </Typography>
              <div className="flex gap-2">
                <Button
                  variant="outlined" size="sm"
                  disabled={currentPage === 1 || loading}
                  onClick={() => setCurrentPage(p => p - 1)}
                >
                  ← Prev
                </Button>
                <Button
                  variant="outlined" size="sm"
                  disabled={currentPage >= totalPages || loading}
                  onClick={() => setCurrentPage(p => p + 1)}
                >
                  Next →
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardBody className="overflow-x-auto p-0">
          {loading ? (
            <div className="flex flex-col justify-center py-24 items-center gap-4">
              <Spinner className="h-10 w-10 text-blue-500" />
              <Typography variant="small" className="text-gray-500">Loading Amazon data…</Typography>
            </div>
          ) : (
            <table className="w-full min-w-max table-auto text-left">
              <thead>
                <tr>
                  {COLUMNS.map((col) => (
                    <th
                      key={col.key}
                      className={`${col.width} border-y border-blue-gray-100 bg-blue-gray-50/50 p-4`}
                    >
                      <Typography
                        variant="small"
                        color="blue-gray"
                        className="flex items-center gap-2 font-bold leading-none opacity-70 whitespace-nowrap"
                      >
                        {col.label}
                        <ChevronUpDownIcon strokeWidth={2} className="h-4 w-4" />
                      </Typography>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageData.length > 0 ? (
                  pageData.map((row, index) => (
                    <tr key={row.id || index} className="even:bg-blue-gray-50/50 hover:bg-blue-50 transition-colors">
                      {COLUMNS.map((col) => (
                        <td key={col.key} className="p-4 border-b border-blue-gray-50">
                          <Typography variant="small" color="blue-gray" className="font-normal">
                            {renderCell(col, row)}
                          </Typography>
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={COLUMNS.length} className="p-20 text-center">
                      <Typography variant="h6" color="blue-gray" className="opacity-40 italic">
                        {error || "No products found"}
                      </Typography>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
};

export default AmazonData;
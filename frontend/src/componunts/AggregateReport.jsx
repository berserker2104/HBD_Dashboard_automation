import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Typography,
  Spinner,
  Button,
} from "@material-tailwind/react";
import {
  GlobeAmericasIcon,
  MapPinIcon,
  TagIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ArrowLongRightIcon,
  QueueListIcon,
  BuildingOffice2Icon,
} from "@heroicons/react/24/solid";
import SlotCounter from "react-slot-counter";
import api from "../utils/Api";
import { StatisticsCard } from "../widgets/cards/statistics-card.jsx";

const AGGREGATE_ENDPOINT = "/report/aggregate";

export function AggregateReport() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    setLoading(true);
    api.get(AGGREGATE_ENDPOINT)
      .then(response => {
        const d = response.data;
        if (d.status === "ERROR") throw new Error(d.message);
        setData(d);
      })
      .catch(e => setError(e.response?.data?.message || e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => fetchData(), []);

  if (loading) return (
    <div className="flex h-screen items-center justify-center flex-col gap-4 bg-gray-50">
      <Spinner className="h-12 w-12 text-blue-500" />
      <Typography color="gray" className="font-medium animate-pulse">Syncing Aggregate Analytics...</Typography>
    </div>
  );

  if (error) return (
    <div className="flex h-screen items-center justify-center p-4 bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-xl text-center border border-red-50">
        <ExclamationCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <Typography variant="h4" color="blue-gray" className="mb-2 font-black">Sync Failure</Typography>
        <Typography className="text-gray-500 mb-8 font-medium">{error}</Typography>
        <Button color="blue-gray" onClick={fetchData} className="flex items-center gap-2 mx-auto normal-case shadow-md">
          <ArrowPathIcon className="h-4 w-4" /> Try Reconnecting
        </Button>
      </div>
    </div>
  );

  const { summary = {}, cities = [], categories = [] } = data;
  const num = (v) => parseInt(v, 10) || 0;

  // Formatting for cards
  const renderValue = (val) => <SlotCounter value={num(val).toLocaleString()} />;
  const linkFooter = (path, label = "View Detailed Report") => (
    <Link to={path} className="flex items-center gap-1 text-[10px] font-black uppercase text-blue-gray-400 hover:text-blue-500 transition-colors">
      {label} <ArrowLongRightIcon className="h-3 w-3" />
    </Link>
  );

  return (
    <div className="p-6 bg-gray-50/50 min-h-screen space-y-12">

      {/* --- PAGE HEADER --- */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-gray-200 pb-8 gap-4">
        <div>
          <Typography variant="h2" color="blue-gray" className="font-black tracking-tight leading-none mb-2">
            Aggregate Report
          </Typography>
          <Typography className="text-gray-500 font-medium max-w-md">
            Consolidated intelligence from the dashboard summary database.
          </Typography>
        </div>
        <div className="bg-white px-6 py-3 rounded-2xl shadow-sm border border-gray-100 text-right">
          <Typography className="text-[10px] font-bold text-blue-gray-300 uppercase tracking-widest mb-1">Total Master Records</Typography>
          <Typography variant="h2" color="blue-gray" className="font-black">
            {renderValue(summary.total_records)}
          </Typography>
        </div>
      </div>

      {/* --- OVERVIEW & PENDING --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <StatisticsCard
          title="Total Combined Records"
          value={renderValue(summary.total_records)}
          color="gray"
          icon={<QueueListIcon className="w-6 h-6 text-white" />}
          footer={linkFooter("/dashboard/home2", "View Listing Report")}
        />
        <StatisticsCard
          title="Pending Data Count"
          value={renderValue(summary.pending_data)}
          color="orange"
          icon={<XCircleIcon className="w-6 h-6 text-white" />}
          footer={linkFooter("/dashboard/cities-pending-report", "Solve Pending Items")}
        />
      </div>

      {/* --- STATE COVERAGE --- */}
      <section>
        <Typography variant="h5" color="blue-gray" className="mb-4 font-black flex items-center gap-2">
          <GlobeAmericasIcon className="h-6 w-6 text-blue-500" /> State Coverage
        </Typography>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatisticsCard title="Total States" value={renderValue(summary.total_states)} color="blue" icon={<GlobeAmericasIcon className="w-6 h-6 text-white" />} />
          <StatisticsCard title="Matched States" value={renderValue(summary.matched_states)} color="green" icon={<CheckCircleIcon className="w-6 h-6 text-white" />} />
          <Link to="/dashboard/masterdata/unmatched-data-review?type=state">
            <StatisticsCard title="Unmatched States" value={renderValue(summary.unmatched_states)} color="red" icon={<XCircleIcon className="w-6 h-6 text-white" />} />
          </Link>
        </div>
      </section>

      {/* --- CITY COVERAGE --- */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <Typography variant="h5" color="blue-gray" className="font-black flex items-center gap-2">
            <MapPinIcon className="h-6 w-6 text-emerald-500" /> City Coverage
          </Typography>
          <Link to="/dashboard/cities-report" className="text-xs font-bold text-blue-500 hover:underline">Full City Analysis →</Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatisticsCard title="Total Cities" value={renderValue(summary.total_cities)} color="emerald" icon={<MapPinIcon className="w-6 h-6 text-white" />} />
          <StatisticsCard title="Matched Cities" value={renderValue(summary.matched_cities)} color="teal" icon={<CheckCircleIcon className="w-6 h-6 text-white" />} />
          <Link to="/dashboard/masterdata/unmatched-data-review?type=city">
            <StatisticsCard title="Unmatched Cities" value={renderValue(summary.unmatched_cities)} color="deep-orange" icon={<XCircleIcon className="w-6 h-6 text-white" />} />
          </Link>
        </div>
      </section>

      {/* --- AREA COVERAGE --- */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <Typography variant="h5" color="blue-gray" className="font-black flex items-center gap-2">
            <MapPinIcon className="h-6 w-6 text-cyan-500" /> Area Coverage
          </Typography>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatisticsCard title="Total Areas" value={renderValue(summary.total_areas)} color="cyan" icon={<MapPinIcon className="w-6 h-6 text-white" />} />
          <StatisticsCard title="Matched Areas" value={renderValue(summary.matched_areas)} color="light-blue" icon={<CheckCircleIcon className="w-6 h-6 text-white" />} />
          <Link to="/dashboard/masterdata/unmatched-data-review?type=area">
            <StatisticsCard title="Unmatched Areas" value={renderValue(summary.unmatched_areas)} color="blue" icon={<XCircleIcon className="w-6 h-6 text-white" />} />
          </Link>
        </div>
      </section>

      {/* --- CATEGORY COVERAGE --- */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <Typography variant="h5" color="blue-gray" className="font-black flex items-center gap-2">
            <TagIcon className="h-6 w-6 text-indigo-500" /> Category Coverage
          </Typography>
          <Link to="/dashboard/categories-report" className="text-xs font-bold text-blue-500 hover:underline">Full Category Analysis →</Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatisticsCard title="Total Categories" value={renderValue(summary.total_categories)} color="indigo" icon={<TagIcon className="w-6 h-6 text-white" />} />
          <StatisticsCard title="Matched Categories" value={renderValue(summary.matched_categories)} color="deep-purple" icon={<CheckCircleIcon className="w-6 h-6 text-white" />} />
          <Link to="/dashboard/masterdata/unmatched-data-review?type=business_category">
            <StatisticsCard title="Unmatched Categories" value={renderValue(summary.unmatched_categories)} color="pink" icon={<XCircleIcon className="w-6 h-6 text-white" />} />
          </Link>
        </div>
      </section>



      <footer className="pt-12 border-t border-gray-200 text-center pb-8">
        <Typography variant="small" className="font-bold text-blue-gray-300 uppercase tracking-widest">
          © {new Date().getFullYear()} HBD Dashboard • Intelligence Protocol Active
        </Typography>
      </footer>
    </div>
  );
}

export default AggregateReport;

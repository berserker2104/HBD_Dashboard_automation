import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Card,
  CardBody,
  Typography,
  Button,
  Progress,
} from "@material-tailwind/react";
import {
  ArchiveBoxIcon,
  MapPinIcon,
  TagIcon,
  ArrowLongRightIcon,
  ServerStackIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartPieIcon,
} from "@heroicons/react/24/solid";
import SlotCounter from "react-slot-counter";

export function ReportDashboard() {
  const [stats, setStats] = useState({
    loading: true,
    data: null,
    topCitiesBusinessData: [],
  });

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const response = await fetch("http://localhost:8001/api/report/aggregate");
        if (!response.ok) throw new Error("API failed");
        const d = await response.json();

        if (d.status === "COMPLETED" && d.summary) {
          setStats({
            loading: false,
            data: d.summary,
            topCitiesBusinessData: d.top_cities_business_data || [],
          });
        } else {
          setStats((prev) => ({ ...prev, loading: false }));
        }
      } catch (error) {
        console.error("error fetching report statistics:", error);
        setStats((prev) => ({ ...prev, loading: false }));
      }
    };

    fetchReportData();
  }, []);

  if (stats.loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Typography variant="h5" color="blue-gray">Loading Dashboard Analytics...</Typography>
      </div>
    );
  }

  const d = stats.data || {};

  // KPI Calculations
  const totalMasterData = d.total_master_data || d.total_records || 0;
  const pendingMasterData = d.pending_master_data || d.pending_data || 0;

  // Coverage Progress Math
  const matchAreas = d.matched_master_areas || d.matched_areas || 0;
  const totalAreas = d.total_location_master_areas || d.total_areas || 1;
  const areaProgress = Math.round((matchAreas / totalAreas) * 100) || 0;

  const matchStates = d.matched_master_states || d.matched_states || 0;
  const totalStates = d.total_location_master_states || d.total_states || 1;
  const stateProgress = Math.round((matchStates / totalStates) * 100) || 0;

  const matchCities = d.matched_master_cities || d.matched_cities || 0;
  const totalCities = d.total_location_master_cities || d.total_cities || 1;
  const cityProgress = Math.round((matchCities / totalCities) * 100) || 0;

  const matchCategories = d.matched_categories_master || d.matched_categories || 0;
  const totalCategories = d.total_master_categories || d.total_categories || 1;
  const categoryProgress = Math.round((matchCategories / totalCategories) * 100) || 0;

  // Unmatched
  const unmatchedStates = d.unmatched_master_states || d.unmatched_states || 0;
  const unmatchedCities = d.unmatched_master_cities || d.unmatched_cities || 0;
  const unmatchedCategories = d.unmatched_category_master || d.unmatched_categories || 0;

  const ProgressCard = ({ title, match, total, progress, color, colorClass }) => (
    <Card className="border border-gray-100 shadow-sm relative overflow-hidden">
      <CardBody className="p-4">
        <Typography variant="small" className="font-bold text-gray-500 mb-2 uppercase">{title}</Typography>
        <div className="flex justify-between items-end mb-2">
          <Typography variant="h4" color="blue-gray" className="font-black">
            {match.toLocaleString()} <span className="text-sm font-normal text-gray-500">/ {total.toLocaleString()}</span>
          </Typography>
          <Typography variant="h6" className={colorClass + " font-bold"}>
            {progress}%
          </Typography>
        </div>
        <Progress value={progress} color={color} size="sm" className="rounded-full bg-gray-100" />
      </CardBody>
    </Card>
  );

  const topCitiesBusinessData = stats.topCitiesBusinessData || [];
  const topCitiesWithBusiness = topCitiesBusinessData.filter(
    (city) => Number(city.business_count || 0) > 0
  );
  const pendingCities = topCitiesBusinessData.filter(
    (city) => Number(city.business_count || 0) === 0
  );

  return (
    <div className="mt-8 flex w-full flex-col gap-8 min-h-screen pb-10 px-4 xl:px-8 bg-slate-50/50">

      {/* 1. TOP ROW: High-Level KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Total Data Volume */}
        <Card className="border border-blue-100 bg-gradient-to-br from-blue-50 to-white shadow-sm overflow-hidden group">
          <CardBody className="p-6 relative">
            <div className="absolute right-0 top-0 p-6 opacity-10 transition-transform group-hover:scale-110">
              <ServerStackIcon className="h-24 w-24 text-blue-500" />
            </div>
            <Typography variant="h6" className="text-blue-600 mb-2 font-bold uppercase tracking-wider">Total Data Volume</Typography>
            <Typography variant="h1" color="blue-gray" className="font-black text-5xl">
              <SlotCounter value={totalMasterData} duration={1} autoAnimationStart={true} />
            </Typography>
            <Typography className="text-gray-500 mt-2 text-sm">Records consolidated in master_table</Typography>
          </CardBody>
        </Card>

        {/* Scraping Progress % */}
        <Card className="border border-green-100 bg-gradient-to-br from-green-50 to-white shadow-sm overflow-hidden">
          <CardBody className="p-6 flex flex-col justify-center items-center h-full">
            <Typography variant="h6" className="text-green-600 mb-4 font-bold uppercase tracking-wider self-start">Area Coverage</Typography>
            <div className="relative flex justify-center items-center w-full">
              {/* Circular rough simulation using a large gauge or progress */}
              <div className="w-full flex flex-col items-center justify-center">
                <Typography variant="h1" className="text-green-500 font-extrabold text-6xl">
                  <SlotCounter value={areaProgress} />%
                </Typography>
                <Typography className="text-gray-500 text-sm mt-4 font-medium px-4 py-1.5 bg-green-100/50 rounded-full">
                  {matchAreas.toLocaleString()} of {totalAreas.toLocaleString()} Areas Matched
                </Typography>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Pending Tasks */}
        <Card className="border border-orange-100 bg-gradient-to-br from-orange-50 to-white shadow-sm overflow-hidden group">
          <CardBody className="p-6 relative">
            <div className="absolute right-0 top-0 p-6 opacity-10 transition-transform group-hover:scale-110">
              <ClockIcon className="h-24 w-24 text-orange-500" />
            </div>
            <Typography variant="h6" className="text-orange-600 mb-2 font-bold uppercase tracking-wider">Pending Tasks</Typography>
            <Typography variant="h1" color="blue-gray" className="font-black text-5xl">
              <SlotCounter value={pendingMasterData} duration={1} autoAnimationStart={true} />
            </Typography>
            <Typography className="text-gray-500 mt-2 text-sm">Records waiting to be processed</Typography>
            <Link to="/report-data" className="mt-4 inline-block">
              <Button size="sm" variant="text" color="orange" className="p-0 hover:bg-transparent flex items-center gap-1 group-hover:gap-2 transition-all">
                View List <ArrowLongRightIcon className="h-4 w-4" />
              </Button>
            </Link>
          </CardBody>
        </Card>

      </div>

      {/* 4. SPECIAL ALERT WIDGET */}
      {unmatchedStates > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg shadow-sm flex items-start gap-4">
          <ExclamationTriangleIcon className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <Typography variant="h6" color="red" className="font-bold">⚠️ Data Alert: {unmatchedStates} State(s) completely unmatched</Typography>
            <Typography className="text-gray-700 mt-1 text-sm">
              In your master data, there are state records that do not match the official Location Master.
              <br /><strong>Action Required:</strong> Check for specific records like "OdishaPondicherry", "Unknown", or spelling mistakes in states.
            </Typography>
          </div>
        </div>
      )}

      {/* 2. MIDDLE ROW: Coverage Analytics */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <MapPinIcon className="h-5 w-5 text-gray-500" />
          <Typography variant="h5" color="blue-gray" className="font-bold">Geographic Coverage Analytics</Typography>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <ProgressCard title="State Coverage" match={matchStates} total={totalStates} progress={stateProgress} color={stateProgress > 90 ? "green" : "orange"} colorClass={stateProgress > 90 ? "text-green-500" : "text-orange-500"} />
          <ProgressCard title="City Coverage" match={matchCities} total={totalCities} progress={cityProgress} color={cityProgress > 80 ? "green" : (cityProgress > 50 ? "blue" : "orange")} colorClass={cityProgress > 80 ? "text-green-500" : (cityProgress > 50 ? "text-blue-500" : "text-orange-500")} />
          <ProgressCard title="Area Coverage" match={matchAreas} total={totalAreas} progress={areaProgress} color={areaProgress > 80 ? "green" : "blue"} colorClass={areaProgress > 80 ? "text-green-500" : "text-blue-500"} />
          <ProgressCard title="Category Match" match={matchCategories} total={totalCategories} progress={categoryProgress} color="blue" colorClass="text-blue-500" />
        </div>
      </div>

      {/* 3. BOTTOM ROW: Data Quality / Action Items */}
      <div>
        <div className="flex items-center gap-2 mb-4 mt-4">
          <ChartBarIcon className="h-5 w-5 text-gray-500" />
          <Typography variant="h5" color="blue-gray" className="font-bold">Data Accuracy (Action Items)</Typography>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          <Card className="border border-gray-100 shadow-sm">
            <CardBody className="p-6">
              <Typography variant="h6" color="blue-gray" className="mb-4">City Health</Typography>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  <Typography className="text-gray-600 font-medium">Matched</Typography>
                </div>
                <Typography className="font-bold">{matchCities}</Typography>
              </div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <XCircleIcon className="h-5 w-5 text-red-500" />
                  <Typography className="text-gray-600 font-medium">Errors</Typography>
                </div>
                <Link to="/dashboard/masterdata/unmatched-data-review?type=city">
                  <Typography className="font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded cursor-pointer hover:bg-red-100 transition-colors" title="Click to view city errors">
                    {unmatchedCities}
                  </Typography>
                </Link>
              </div>
              <Progress value={Math.round((matchCities / (matchCities + unmatchedCities || 1)) * 100)} color="green" className="bg-red-100" />
              <Typography className="text-xs text-center mt-3 text-gray-500">Fix the {unmatchedCities} city errors in the master data</Typography>
            </CardBody>
          </Card>

          <Card className="border border-gray-100 shadow-sm md:col-span-2">
            <CardBody className="p-6">
              <Typography variant="h6" color="blue-gray" className="mb-4">Category Health</Typography>
              <div className="flex flex-col md:flex-row gap-8 items-center h-full pb-4">

                <div className="w-full flex-1 space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <Typography className="text-sm font-medium text-gray-600">Matched Categories</Typography>
                      <Typography className="text-sm font-bold text-green-600">{matchCategories}</Typography>
                    </div>
                    <Progress value={Math.round((matchCategories / (matchCategories + unmatchedCategories || 1)) * 100)} color="blue" className="bg-gray-100" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <Typography className="text-sm font-medium text-gray-600">Unmatched (New Categories)</Typography>
                      <Link to="/dashboard/masterdata/unmatched-data-review?type=business_category">
                        <Typography className="text-sm font-bold text-orange-600 hover:text-orange-800 cursor-pointer underline">{unmatchedCategories}</Typography>
                      </Link>
                    </div>
                    <Progress value={Math.round((unmatchedCategories / (matchCategories + unmatchedCategories || 1)) * 100)} color="orange" className="bg-gray-100" />
                  </div>
                </div>

                <div className="flex-1 bg-yellow-50/50 p-4 rounded-xl border border-yellow-100">
                  <div className="flex items-start gap-3">
                    <div className="mt-1 bg-yellow-100 p-1.5 rounded-lg"><TagIcon className="h-5 w-5 text-yellow-700" /></div>
                    <div>
                      <Typography className="font-bold text-yellow-800 text-sm mb-1">Insight Required</Typography>
                      <Typography className="text-xs text-yellow-700 leading-relaxed">
                        Your unmatched category rate is quite high ({unmatchedCategories}). This suggests your scraper is finding many new business categories that aren't mapped to your official master list yet. Reviewing these will heavily improve grouping.
                      </Typography>
                    </div>
                  </div>
                </div>

              </div>
            </CardBody>
          </Card>

        </div>
      </div>

      {topCitiesWithBusiness.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center gap-2 mb-4">
            <MapPinIcon className="h-5 w-5 text-gray-500" />
            <Typography variant="h5" color="blue-gray" className="font-bold">
              Top Cities Business Data
            </Typography>
          </div>

          <Card className="h-full w-full overflow-scroll border border-gray-100 shadow-sm max-h-[500px]">
            <table className="w-full min-w-max table-auto text-left">
              <thead>
                <tr>
                  {["City Rank", "City Name", "State Name", "Business Count"].map((heading) => (
                    <th key={heading} className="border-b border-blue-gray-100 bg-blue-gray-50 p-4 sticky top-0 z-10">
                      <Typography variant="small" color="blue-gray" className="font-bold leading-none opacity-70">
                        {heading}
                      </Typography>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topCitiesWithBusiness.map((cityData, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" color="blue-gray">{cityData.city_rank}</Typography>
                    </td>
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" color="blue-gray">{cityData.city_name}</Typography>
                    </td>
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" color="blue-gray">{cityData.state_name}</Typography>
                    </td>
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" color="blue-gray">{Number(cityData.business_count || 0).toLocaleString()}</Typography>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {pendingCities.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center gap-2 mb-4">
            <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />
            <Typography variant="h5" color="blue-gray" className="font-bold">
              Pending Cities Data
            </Typography>
          </div>

          <Card className="h-full w-full overflow-scroll border border-gray-100 shadow-sm max-h-[500px]">
            <table className="w-full min-w-max table-auto text-left">
              <thead>
                <tr>
                  {["City Rank", "City Name", "State Name"].map((heading) => (
                    <th key={heading} className="border-b border-blue-gray-100 bg-orange-50 p-4 sticky top-0 z-10">
                      <Typography variant="small" color="blue-gray" className="font-bold leading-none opacity-70">
                        {heading}
                      </Typography>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pendingCities.map((cityData, index) => (
                  <tr key={index} className="hover:bg-orange-50/30 transition-colors">
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" className="font-normal text-orange-800">{cityData.city_rank}</Typography>
                    </td>
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" className="font-normal text-orange-800">{cityData.city_name}</Typography>
                    </td>
                    <td className="p-4 border-b border-blue-gray-50">
                      <Typography variant="small" className="font-normal text-orange-800">{cityData.state_name}</Typography>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

    </div>
  );
}

export default ReportDashboard;
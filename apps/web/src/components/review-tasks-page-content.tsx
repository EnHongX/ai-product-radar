"use client";

import { useEffect, useState } from "react";
import { Eye, X, ExternalLink, CheckCircle, XCircle, Clock, ChevronRight, ChevronDown } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { useLanguage } from "@/i18n";
import type { ReviewTaskListItem, ReviewTask, ReviewStats, ReviewSubmitRequest } from "@/lib/api";
import { fetchReviewTasks, fetchReviewStats, fetchReviewTask, submitReview } from "@/lib/api";

type ReviewStatusFilter = "all" | "pending" | "approved" | "rejected";

export function ReviewTasksPageContent() {
  const { t } = useLanguage();
  const [tasks, setTasks] = useState<ReviewTaskListItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<ReviewStatusFilter>("pending");
  const [selectedTask, setSelectedTask] = useState<ReviewTask | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, tasksData] = await Promise.all([
        fetchReviewStats(),
        fetchReviewTasks(statusFilter === "all" ? undefined : statusFilter, 50, 0),
      ]);
      setStats(statsData);
      setTasks(tasksData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleViewDetail = async (task: ReviewTaskListItem) => {
    try {
      setDetailLoading(true);
      setShowDetailModal(true);
      setReviewNotes("");
      const detail = await fetchReviewTask(task.id);
      setSelectedTask(detail);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review task detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setShowDetailModal(false);
    setSelectedTask(null);
    setReviewNotes("");
  };

  const handleSubmitReview = async (approved: boolean) => {
    if (!selectedTask) return;

    const confirmMessage = approved
      ? t.reviewTasks.confirmApprove
      : t.reviewTasks.confirmReject;

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setSubmitting(true);
      const request: ReviewSubmitRequest = {
        approved,
        notes: reviewNotes || undefined,
      };
      await submitReview(selectedTask.id, request);
      setSuccessMessage(approved ? t.reviewTasks.approveSuccess : t.reviewTasks.rejectSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      handleCloseDetail();
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString();
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case "pending":
        return { label: t.reviewTasks.pending, color: "text-yellow-600", bg: "bg-yellow-100" };
      case "approved":
        return { label: t.reviewTasks.approved, color: "text-green-600", bg: "bg-green-100" };
      case "rejected":
        return { label: t.reviewTasks.rejected, color: "text-red-600", bg: "bg-red-100" };
      default:
        return { label: status, color: "text-gray-600", bg: "bg-gray-100" };
    }
  };

  const getPriorityDisplay = (priority: number) => {
    if (priority >= 1) return { label: t.reviewTasks.high, color: "text-red-600" };
    if (priority <= -1) return { label: t.reviewTasks.low, color: "text-gray-500" };
    return { label: t.reviewTasks.normal, color: "text-blue-600" };
  };

  const getReleaseTypeDisplay = (releaseType: string) => {
    switch (releaseType) {
      case "new":
        return t.reviewTasks.newRelease;
      case "update":
        return t.reviewTasks.update;
      case "beta":
        return t.reviewTasks.beta;
      default:
        return releaseType;
    }
  };

  const getStatusBadge = (status: string) => {
    const display = getStatusDisplay(status);
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${display.bg} ${display.color}`}>
        {status === "pending" && <Clock className="h-3 w-3" />}
        {status === "approved" && <CheckCircle className="h-3 w-3" />}
        {status === "rejected" && <XCircle className="h-3 w-3" />}
        {display.label}
      </span>
    );
  };

  const allSelected = tasks.length > 0 && statusFilter === "all";
  const pendingSelected = statusFilter === "pending";
  const approvedSelected = statusFilter === "approved";
  const rejectedSelected = statusFilter === "rejected";

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{t.reviewTasks.title}</h2>
          {stats && (
            <div className="flex items-center gap-4">
              <button
                onClick={() => setStatusFilter("all")}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  allSelected ? "bg-gray-200 text-ink" : "bg-gray-100 text-muted hover:bg-gray-200"
                }`}
              >
                <span>{t.reviewTasks.total}:</span>
                <span className="font-bold">{stats.total}</span>
              </button>
              <button
                onClick={() => setStatusFilter("pending")}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  pendingSelected ? "bg-yellow-100 text-yellow-800" : "bg-gray-100 text-muted hover:bg-yellow-50"
                }`}
              >
                <Clock className="h-4 w-4" />
                <span>{t.reviewTasks.pending}:</span>
                <span className="font-bold">{stats.pending}</span>
              </button>
              <button
                onClick={() => setStatusFilter("approved")}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  approvedSelected ? "bg-green-100 text-green-800" : "bg-gray-100 text-muted hover:bg-green-50"
                }`}
              >
                <CheckCircle className="h-4 w-4" />
                <span>{t.reviewTasks.approved}:</span>
                <span className="font-bold">{stats.approved}</span>
              </button>
              <button
                onClick={() => setStatusFilter("rejected")}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  rejectedSelected ? "bg-red-100 text-red-800" : "bg-gray-100 text-muted hover:bg-red-50"
                }`}
              >
                <XCircle className="h-4 w-4" />
                <span>{t.reviewTasks.rejected}:</span>
                <span className="font-bold">{stats.rejected}</span>
              </button>
            </div>
          )}
        </div>

        {successMessage && (
          <div className="mx-5 mt-4 rounded-md bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-800">
            {successMessage}
          </div>
        )}

        {error && (
          <div className="mx-5 mt-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <div className="px-5 py-8 text-center text-muted">{t.common.loading}</div>
        ) : tasks.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-muted">{t.reviewTasks.noTasks}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.reviewTasks.status}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.reviewTasks.priority}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden sm:table-cell">
                    {t.reviewTasks.company}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">
                    {t.reviewTasks.articleTitle}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden md:table-cell">
                    {t.reviewTasks.releaseTitle}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">
                    {t.reviewTasks.confidence}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">
                    {t.reviewTasks.createdAt}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-ink">{t.reviewTasks.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {tasks.map((task) => {
                  const priority = getPriorityDisplay(task.priority);
                  return (
                    <tr
                      key={task.id}
                      className={`hover:bg-gray-50 ${
                        task.status === "pending" ? "bg-yellow-50/30" : ""
                      }`}
                    >
                      <td className="px-4 py-3">{getStatusBadge(task.status)}</td>
                      <td className="px-4 py-3">
                        <span className={`text-sm font-medium ${priority.color}`}>
                          {priority.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <span className="text-sm text-muted">{task.company_name || "-"}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col">
                          <span
                            className="text-sm font-medium text-ink truncate max-w-[200px]"
                            title={task.article_title || ""}
                          >
                            {task.article_title || "-"}
                          </span>
                          <span className="text-xs text-muted sm:hidden">
                            {task.company_name || "-"}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span
                          className="text-sm text-ink truncate max-w-[250px] block"
                          title={task.release_title || ""}
                        >
                          {task.release_title || "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-sm text-ink">
                          {task.confidence_score !== null && task.confidence_score !== undefined
                            ? `${(task.confidence_score * 100).toFixed(0)}%`
                            : "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-sm text-muted">{formatDate(task.created_at)}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleViewDetail(task)}
                          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          {t.reviewTasks.view}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showDetailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <div className="flex items-center gap-3">
                <h3 className="text-base font-semibold text-ink">{t.reviewTasks.viewDetail}</h3>
                {selectedTask && getStatusBadge(selectedTask.status)}
              </div>
              <button
                onClick={handleCloseDetail}
                className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {detailLoading ? (
                <div className="text-center py-8 text-muted">{t.common.loading}</div>
              ) : selectedTask ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted">{t.reviewTasks.company}</label>
                      <p className="text-ink mt-1">{selectedTask.company?.name || "-"}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted">{t.reviewTasks.source}</label>
                      <p className="text-ink mt-1">{selectedTask.source?.name || "-"}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted">{t.reviewTasks.status}</label>
                      <p className="mt-1">{getStatusBadge(selectedTask.status)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted">{t.reviewTasks.priority}</label>
                      <p
                        className={`text-ink mt-1 font-medium ${
                          getPriorityDisplay(selectedTask.priority).color
                        }`}
                      >
                        {getPriorityDisplay(selectedTask.priority).label}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted">{t.reviewTasks.createdAt}</label>
                      <p className="text-ink mt-1">{formatDate(selectedTask.created_at)}</p>
                    </div>
                  </div>

                  <div className="border-t border-line pt-6">
                    <h4 className="text-sm font-semibold text-ink mb-4 flex items-center gap-2">
                      <ChevronRight className="h-4 w-4" />
                      {t.reviewTasks.originalArticle}
                    </h4>
                    {selectedTask.raw_article ? (
                      <div className="space-y-4 bg-gray-50 rounded-lg p-4">
                        <div>
                          <label className="text-sm font-medium text-muted">{t.reviewTasks.articleTitle}</label>
                          <p className="text-ink font-medium mt-1">{selectedTask.raw_article.title}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted">{t.reviewTasks.articleUrl}</label>
                          <a
                            href={selectedTask.raw_article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-accent hover:underline flex items-center gap-1 mt-1 break-all"
                          >
                            {selectedTask.raw_article.url}
                            <ExternalLink className="h-4 w-4 flex-shrink-0" />
                          </a>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.publishedAt || "Published"}</label>
                            <p className="text-ink mt-1">{formatDate(selectedTask.raw_article.published_at)}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.fetchedAt || "Fetched"}</label>
                            <p className="text-ink mt-1">{formatDate(selectedTask.raw_article.fetched_at)}</p>
                          </div>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted">{t.reviewTasks.content || "Content"}</label>
                          <div className="mt-1 p-4 bg-white rounded-md border border-line max-h-[300px] overflow-y-auto">
                            {selectedTask.raw_article.content ? (
                              <pre className="text-sm text-ink whitespace-pre-wrap break-words">
                                {selectedTask.raw_article.content}
                              </pre>
                            ) : (
                              <p className="text-muted">{t.common.noData}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-muted">{t.common.noData}</p>
                    )}
                  </div>

                  <div className="border-t border-line pt-6">
                    <h4 className="text-sm font-semibold text-ink mb-4 flex items-center gap-2">
                      <ChevronRight className="h-4 w-4" />
                      {t.reviewTasks.extractedResult}
                    </h4>
                    {selectedTask.product_release ? (
                      <div className="space-y-4 bg-blue-50 rounded-lg p-4">
                        <div>
                          <label className="text-sm font-medium text-muted">{t.reviewTasks.releaseTitle}</label>
                          <p className="text-ink font-medium mt-1">
                            {selectedTask.product_release.release_title}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted">{t.reviewTasks.releaseUrl}</label>
                          <a
                            href={selectedTask.product_release.release_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-accent hover:underline flex items-center gap-1 mt-1 break-all"
                          >
                            {selectedTask.product_release.release_url}
                            <ExternalLink className="h-4 w-4 flex-shrink-0" />
                          </a>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.releaseType}</label>
                            <p className="text-ink mt-1">
                              {getReleaseTypeDisplay(selectedTask.product_release.release_type)}
                            </p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.confidence}</label>
                            <p className="text-ink mt-1">
                              {selectedTask.product_release.confidence_score !== null &&
                              selectedTask.product_release.confidence_score !== undefined
                                ? `${(selectedTask.product_release.confidence_score * 100).toFixed(0)}%`
                                : "-"}
                            </p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.reviewStatus || "Review Status"}</label>
                            <p className="text-ink mt-1">
                              {selectedTask.product_release.review_status}
                            </p>
                          </div>
                        </div>
                        {selectedTask.product_release.summary && (
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.summary}</label>
                            <p className="text-ink mt-1">{selectedTask.product_release.summary}</p>
                          </div>
                        )}
                        {selectedTask.product_release.extraction_payload && (
                          <div>
                            <label className="text-sm font-medium text-muted">{t.reviewTasks.extractionPayload}</label>
                            <div className="mt-1 p-4 bg-white rounded-md border border-line max-h-[200px] overflow-y-auto">
                              <pre className="text-xs text-ink whitespace-pre-wrap break-words">
                                {JSON.stringify(selectedTask.product_release.extraction_payload, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted">{t.common.noData}</p>
                    )}
                  </div>

                  {selectedTask.status === "pending" && (
                    <div className="border-t border-line pt-6">
                      <label className="text-sm font-medium text-muted block mb-2">{t.reviewTasks.notes}</label>
                      <textarea
                        value={reviewNotes}
                        onChange={(e) => setReviewNotes(e.target.value)}
                        placeholder={t.reviewTasks.notesPlaceholder}
                        className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                        rows={3}
                      />
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className="flex justify-between border-t border-line px-5 py-4">
              <button
                onClick={handleCloseDetail}
                className="inline-flex items-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-200 transition-colors"
              >
                {t.reviewTasks.close}
              </button>
              {selectedTask && selectedTask.status === "pending" && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleSubmitReview(false)}
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <XCircle className="h-4 w-4" />
                    {submitting ? "..." : t.reviewTasks.reject}
                  </button>
                  <button
                    onClick={() => handleSubmitReview(true)}
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <CheckCircle className="h-4 w-4" />
                    {submitting ? "..." : t.reviewTasks.approve}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}

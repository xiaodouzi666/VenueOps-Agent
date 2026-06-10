import { FileSearch } from "lucide-react";
import type { EvidenceDoc } from "@/lib/types";

export function EvidencePanel({ evidence }: { evidence: EvidenceDoc[] }) {
  return (
    <div className="evidenceList">
      {evidence.length === 0 ? (
        <p className="miniText muted">SOP evidence appears after an agent run.</p>
      ) : (
        evidence.map((doc) => (
          <div className="evidenceItem" key={doc._id}>
            <div className="rowTop">
              <strong><FileSearch size={14} /> {doc.title}</strong>
              <span className="pill">score {doc.score.toFixed(2)}</span>
            </div>
            <p className="miniText muted">{doc.content}</p>
            <div className="evidenceTags">
              {doc.tags.slice(0, 6).map((tag) => <span className="tag" key={tag}>{tag}</span>)}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

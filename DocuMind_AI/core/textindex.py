"""Text index: builds document text from OCR words while remembering which OCR
word produced each character. This is what lets every extracted fact and every
answer be traced back to boxes on the image."""
import bisect


class DocIndex:
    def __init__(self, words):
        self.words = words
        self.text = ""
        self.lines = []          # {"text","ids","page","start","end"}
        self._starts, self._ends, self._wids = [], [], []
        self._word_conf = dict(zip(words["word_id"], words["conf"])) if len(words) else {}
        parts, pos, prev_page = [], 0, None
        if len(words):
            for (page, _b, _p, _l), g in words.groupby(
                    ["page", "block", "par", "line"], sort=False):
                g = g.sort_values("left")
                if prev_page is not None and page != prev_page:
                    parts.append("\n"); pos += 1          # blank line between pages
                line_start = pos
                for _, w in g.iterrows():
                    t = str(w["text"])
                    self._starts.append(pos); self._ends.append(pos + len(t))
                    self._wids.append(int(w["word_id"]))
                    parts.append(t); pos += len(t)
                    parts.append(" "); pos += 1
                parts[-1] = "\n"                          # replace trailing space
                self.lines.append({"text": " ".join(g["text"].astype(str)),
                                   "ids": [int(i) for i in g["word_id"]],
                                   "page": int(page), "start": line_start,
                                   "end": pos - 1})
                prev_page = page
        self.text = "".join(parts)
        self._line_starts = [l["start"] for l in self.lines]

    def ids_in_span(self, start, end):
        """OCR word ids whose characters overlap [start, end)."""
        out = []
        i = bisect.bisect_left(self._ends, start + 1)
        while i < len(self._starts) and self._starts[i] < end:
            out.append(self._wids[i]); i += 1
        return out

    def line_index_at(self, pos):
        i = bisect.bisect_right(self._line_starts, pos) - 1
        return max(i, 0)

    def mean_conf(self, ids):
        vals = [self._word_conf[i] for i in ids if i in self._word_conf]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    def page_of(self, ids):
        if not ids:
            return 1
        row = self.words[self.words["word_id"] == ids[0]]
        return int(row["page"].iloc[0]) if len(row) else 1

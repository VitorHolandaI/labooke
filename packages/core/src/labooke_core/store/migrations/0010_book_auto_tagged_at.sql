-- 0010 - Record when the LLM last classified a book against the tag list.
--
-- book_tags does not say who attached a tag, and a run that finds no fitting
-- tag attaches nothing, so the admin page needs this to tell done from
-- never-tried. ISO-8601 UTC text; NULL means never auto-tagged.

ALTER TABLE books ADD COLUMN auto_tagged_at TEXT;

import pandas as pd


def split_tags(tag_value):
    if not tag_value:
        return []
    if isinstance(tag_value, list):
        return [t.strip() for t in tag_value if str(t).strip()]
    return [t.strip() for t in str(tag_value).split(",") if t.strip()]


def join_tags(tags):
    if not tags:
        return None
    return ",".join([t.strip() for t in tags if str(t).strip()])


def normalize_tag_value(tag_value):
    if pd.isna(tag_value):
        return ""
    return str(tag_value).strip()


def ensure_tags_exist(db, tags):
    for t in split_tags(tags):
        db.add_tag(t)


def filter_df_by_tags(df, tag_list, column="tags"):
    if df.empty or not tag_list:
        return df
    target = set(tag_list)
    return df[df[column].fillna("").astype(str).apply(lambda x: any(tag in split_tags(x) for tag in target))]

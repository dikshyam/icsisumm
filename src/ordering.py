def by_date(sentences):
    return sorted(sentences, lambda x, y: cmp(x.order, y.order) if x.date == y.date else cmp(x.date, y.date))

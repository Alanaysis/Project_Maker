package stream

type TopK struct {
	k      int
	items  map[string]int
	minKey string
}

func NewTopK(k int) *TopK {
	return &TopK{
		k:     k,
		items: make(map[string]int),
	}
}

func (tk *TopK) Add(item string) {
	if count, exists := tk.items[item]; exists {
		tk.items[item] = count + 1
		if item == tk.minKey {
			tk.updateMin()
		}
		return
	}
	if len(tk.items) < tk.k {
		tk.items[item] = 1
		tk.updateMin()
		return
	}
	delete(tk.items, tk.minKey)
	tk.items[item] = 1
	tk.updateMin()
}

func (tk *TopK) updateMin() {
	first := true
	for k, v := range tk.items {
		if first || v < tk.items[tk.minKey] {
			tk.minKey = k
			first = false
		}
	}
}

func (tk *TopK) Top() []struct {
	Item  string
	Count int
} {
	result := make([]struct {
		Item  string
		Count int
	}, 0, len(tk.items))
	for k, v := range tk.items {
		result = append(result, struct {
			Item  string
			Count int
		}{k, v})
	}
	for i := 0; i < len(result); i++ {
		for j := i + 1; j < len(result); j++ {
			if result[j].Count > result[i].Count {
				result[i], result[j] = result[j], result[i]
			}
		}
	}
	return result
}

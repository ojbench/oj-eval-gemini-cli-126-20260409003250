#pragma once

#include <iostream>
#include <vector>
#include <string>

inline int row = -1, col = -1;
inline char* cell_state = nullptr;
inline std::vector<int> live_cells;

inline void Initialize() {
    std::cin >> col >> row;
    cell_state = new char[row * col]();
    
    std::string s;
    int r = 0, c = 0;
    while (std::cin >> s) {
        int num = 0;
        bool has_num = false;
        for (char ch : s) {
            if (isdigit(ch)) {
                num = num * 10 + (ch - "0"[0]);
                has_num = true;
            } else if (ch == "b"[0] || ch == "o"[0]) {
                int count = has_num ? num : 1;
                for (int i = 0; i < count; ++i) {
                    if (ch == "o"[0]) {
                        if (r < row && c < col) {
                            int idx = r * col + c;
                            live_cells.push_back(idx);
                            cell_state[idx] |= 16;
                        }
                    }
                    c++;
                }
                num = 0;
                has_num = false;
            } else if (ch == "$"[0]) {
                int count = has_num ? num : 1;
                r += count;
                c = 0;
                num = 0;
                has_num = false;
            } else if (ch == "!"[0]) {
                return;
            }
        }
    }
}

inline void Tick() {
    std::vector<int> next_live_cells;

    // Pass 1: increment neighbor counts
    for (int idx : live_cells) {
        int r = idx / col;
        int c = idx % col;
        for (int dr = -1; dr <= 1; ++dr) {
            for (int dc = -1; dc <= 1; ++dc) {
                if (dr == 0 && dc == 0) continue;
                int nr = r + dr;
                int nc = c + dc;
                if (nr < 0 || nr >= row || nc < 0 || nc >= col) continue;
                int nidx = nr * col + nc;
                cell_state[nidx]++;
            }
        }
    }

    // Pass 2: determine next state
    for (int idx : live_cells) {
        // Process idx itself
        if ((cell_state[idx] & 64) == 0) {
            cell_state[idx] |= 64;
            int count = cell_state[idx] & 15;
            bool is_live = (cell_state[idx] & 16) != 0;
            bool next_live = false;
            if (is_live) {
                if (count == 2 || count == 3) next_live = true;
            } else {
                if (count == 3) next_live = true;
            }
            if (next_live) {
                next_live_cells.push_back(idx);
            }
        }

        // Process neighbors
        int r = idx / col;
        int c = idx % col;
        for (int dr = -1; dr <= 1; ++dr) {
            for (int dc = -1; dc <= 1; ++dc) {
                if (dr == 0 && dc == 0) continue;
                int nr = r + dr;
                int nc = c + dc;
                if (nr < 0 || nr >= row || nc < 0 || nc >= col) continue;
                int nidx = nr * col + nc;
                
                if ((cell_state[nidx] & 64) == 0) {
                    cell_state[nidx] |= 64;
                    int count = cell_state[nidx] & 15;
                    bool is_live = (cell_state[nidx] & 16) != 0;
                    bool next_live = false;
                    if (is_live) {
                        if (count == 2 || count == 3) next_live = true;
                    } else {
                        if (count == 3) next_live = true;
                    }
                    if (next_live) {
                        next_live_cells.push_back(nidx);
                    }
                }
            }
        }
    }

    // Pass 3: clear cell_state
    for (int idx : live_cells) {
        cell_state[idx] = 0;
        int r = idx / col;
        int c = idx % col;
        for (int dr = -1; dr <= 1; ++dr) {
            for (int dc = -1; dc <= 1; ++dc) {
                if (dr == 0 && dc == 0) continue;
                int nr = r + dr;
                int nc = c + dc;
                if (nr < 0 || nr >= row || nc < 0 || nc >= col) continue;
                int nidx = nr * col + nc;
                cell_state[nidx] = 0;
            }
        }
    }

    // Pass 4: set new live cells
    live_cells = std::move(next_live_cells);
    for (int idx : live_cells) {
        cell_state[idx] |= 16;
    }
}

inline void PrintGame() {
    std::cout << col << " " << row << "\n";
    
    int last_live_row = -1;
    for (int r = row - 1; r >= 0; --r) {
        bool has_live = false;
        for (int c = 0; c < col; ++c) {
            if (cell_state[r * col + c] & 16) {
                has_live = true;
                break;
            }
        }
        if (has_live) {
            last_live_row = r;
            break;
        }
    }
    
    if (last_live_row == -1) {
        std::cout << "!\n";
        return;
    }
    
    int empty_rows = 0;
    bool first_live_row_seen = false;
    for (int r = 0; r <= last_live_row; ++r) {
        int last_live_col = -1;
        for (int c = col - 1; c >= 0; --c) {
            if (cell_state[r * col + c] & 16) {
                last_live_col = c;
                break;
            }
        }
        
        if (last_live_col == -1) {
            empty_rows++;
            continue;
        }
        
        int dollars = empty_rows + (first_live_row_seen ? 1 : 0);
        if (dollars > 0) {
            if (dollars > 1) std::cout << dollars;
            std::cout << "$"[0];
        }
        empty_rows = 0;
        first_live_row_seen = true;
        
        int count = 0;
        char current_char = " "[0];
        for (int c = 0; c <= last_live_col; ++c) {
            char ch = (cell_state[r * col + c] & 16) ? "o"[0] : "b"[0];
            if (ch == current_char) {
                count++;
            } else {
                if (count > 0) {
                    if (count > 1) std::cout << count;
                    std::cout << current_char;
                }
                current_char = ch;
                count = 1;
            }
        }
        if (count > 0) {
            if (count > 1) std::cout << count;
            std::cout << current_char;
        }
    }
    std::cout << "!\n";
}

inline int GetLiveCell() {
    return live_cells.size();
}

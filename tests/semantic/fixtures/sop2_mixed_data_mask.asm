; Combine runtime scalar data in s4 and the wave's lane-0 compare mask.
; Each lane writes the same result word followed by a marker for SCC.
v_cmp_eq_u32_e64 s20, 0, v0
s_or_b32 s30, s4, s20
s_cselect_b32 s31, 7, 0
v_mov_b32_e32 v4, s30
v_mov_b32_e32 v5, s31
v_lshlrev_b32_e32 v2, 3, v0
buffer_store_dword v4, v2, s[0:3], 0 offen
buffer_store_dword v5, v2, s[0:3], 0 offen offset:4
s_endpgm

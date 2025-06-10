# 기존 코드 (오류 발생 가능성)
# num_shares = np.floor(amount_per_valid_item / price)
# if num_shares > 0:

# 수정된 코드
num_shares = np.floor(amount_per_valid_item / price)
# num_shares가 Series일 경우, 단일 값으로 추출 (오류 방지)
if isinstance(num_shares, pd.Series):
    if not num_shares.empty:
        num_shares_scalar = num_shares.item() # Series의 유일한 값 추출
    else:
        num_shares_scalar = 0 # 빈 Series일 경우 0으로 처리
else:
    num_shares_scalar = num_shares # 이미 스칼라인 경우 그대로 사용

if num_shares_scalar > 0:
    purchase_amount = num_shares_scalar * price
    st.write(f"- **{name}**: 약 **{purchase_amount:,.0f}원** ({int(num_shares_scalar)}주/개 구매 가능)")
    remaining_amount_for_asset -= purchase_amount
else:
    st.write(f"- **{name}**: **{price:,.0f}원** (1주/개 구매 금액) - 현재 배분 금액으로는 1주/개 구매 어려움.")

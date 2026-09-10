# Hướng dẫn test Transcript Scenario System — PixelClass TIL

File này dùng để test giai đoạn **Transcript-first**. Live Mode tạm để sau. Mục tiêu hiện tại là tạo/chỉnh các kịch bản lớp học cố định 30 phút, chỉnh prompt/parameter của từng student, xem transcript draft, rồi chạy readiness test trước khi dùng cho baseline vs TIL evaluator.

## 1. Chạy hệ thống local

### Backend

```bash
cd D:/Code/til-classroom-sim/backend
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd D:/Code/til-classroom-sim/frontend
export PATH='/c/Program Files/nodejs':"$PATH"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

## 2. UI workflow để test transcript system

1. Mở homepage.
2. Chọn **Transcript Scenario System**.
3. Ở sidebar, chọn một scenario.
4. Kiểm tra metadata:
   - subject;
   - level;
   - 30 minutes;
   - student count;
   - turn count;
   - misconception count.
5. Xem **Learning objectives** và **Misconceptions to surface**.
6. Chỉnh **Student prompt parameters**:
   - confidence;
   - misconception strength;
   - participation style;
   - special prompt instructions.
7. Chỉnh **Draft transcript table** trong một table thật duy nhất:
   - mỗi row là 1 classroom turn;
   - columns: `Turn | Name | Content`;
   - row đầu nên là opening ngắn giống mẫu (`Good morning, everyone.`), không nhét một lecture quá dài vào đầu;
   - explanation nên được chia đều qua các PART theo thời gian: introduction, concept explanation, quick check, worked example, differentiated practice, misconception repair, final review;
   - sửa trực tiếp trong ô `Name` hoặc `Content` của từng row;
   - giữ đúng **64 rows/turns** cho lesson dialogue 30 phút.
8. Nếu cần chỉnh sâu, dùng **Advanced JSON editor** rồi bấm **Apply JSON locally**.
9. Bấm **Save Scenario** để lưu file JSON.
10. Bấm **Save + Run Readiness Test** để kiểm tra scenario có đủ điều kiện test chưa.
11. Khi scenario pass, bấm **Proceed to TIL Evaluation** để chuyển sang bước đánh giá TIL.

## 3. Scenario library hiện có

Hệ thống hiện seed 8 scenarios, mỗi scenario là 30 phút, có **6 nhân vật tiếng Anh cố định theo mẫu classroom dialogue** (`Mr. Anderson`, `Alice`, `Ben`, `Chloe`, `Daniel`, `Lily`, `Noah`) và đúng **64 transcript turns**:

- `hs_python_loops_30m` — Computer Science — college
- `hs_quadratic_functions_30m` — Mathematics — college
- `hs_newton_laws_30m` — Physics — college
- `college_cellular_respiration_30m` — Biology — college
- `college_stoichiometry_30m` — Chemistry — college
- `uni_hypothesis_testing_30m` — Statistics — university
- `uni_microeconomics_elasticity_30m` — Economics — university
- `uni_primary_source_analysis_30m` — History / Humanities — university

Các file scenario nằm ở:

```text
D:/Code/til-classroom-sim/backend/data/transcript_scenarios/
```

Mỗi file là JSON editable. UI cũng đang edit trực tiếp các JSON này qua API.

## 4. Readiness test kiểm tra gì?

Readiness test hiện kiểm tra:

- scenario có đúng 30 phút không;
- có ít nhất 5 lesson phases không;
- phases có cover 0–30 phút không;
- có ít nhất 4 student profiles không;
- mỗi student có prompt instructions/parameters không;
- transcript có đúng 64 turns theo dạng dialogue 30 phút không;
- transcript có opening ngắn, `Class` greeting/closure, và PART 1–7 balanced dialogue không;
- transcript có subject-specific terminology, worked examples, misconceptions, differentiated questions, và enrichment markers không;
- transcript có misconception event không;
- transcript có formative assessment không;
- có editable notes cho researcher không.

Academic source checks for the enriched scenarios are documented in `docs/SCENARIO_ACADEMIC_ACCURACY_NOTES.md`.

Nếu test pass, scenario có thể được dùng làm fixed transcript draft để đưa vào evaluator testing sau.

## 5. Student prompt parameters nên chỉnh thế nào?

Mỗi student có các field quan trọng:

- `confidence`: độ tự tin 0–1.
- `misconception_strength`: độ mạnh của misconception 0–1.
- `participation_style`: cách tham gia lớp học.
- `prior_knowledge`: kiến thức nền.
- `affect`: cảm xúc/trạng thái như anxious, bored, curious.
- `response_length`: short / medium / long.
- `language_level`: level ngôn ngữ học sinh.
- `prompt_instructions`: instruction chính để model đóng vai student.

Ví dụ chỉnh student misconception-heavy:

```text
Confidence: 0.45
Misconception strength: 0.85
Participation style: speaks when teacher asks for prediction
Special instructions: Reveal the misconception clearly, but change your mind if the teacher asks you to test the idea against evidence.
```

## 6. Khi nào cần tài liệu môn học?

Các scenario hiện tại là draft tổng quát, đủ để test hệ thống transcript và flow TIL evaluation. Để generate nội dung bài học **chuyên sâu/chuẩn môn học hơn**, bro nên cung cấp tài liệu môn học liên quan để tôi rewrite transcript theo đúng lesson content, terminology, misconception, và assessment style của tài liệu đó.

Nên gửi cho tôi một trong các loại tài liệu sau:

- slide bài giảng;
- textbook excerpt;
- worksheet;
- rubric chấm bài;
- curriculum outcome;
- lesson plan mẫu;
- assessment question;
- transcript thật hoặc teacher notes nếu có ethics/supervisor approval.

Tài liệu cần nhất khi:

- scenario thuộc môn chuyên sâu;
- muốn wording chính xác theo curriculum;
- cần misconceptions đúng literature;
- muốn expert reviewer thấy scenario credible hơn;
- muốn tạo benchmark transcript mạnh/yếu rõ ràng.

## 7. API endpoints hữu ích

List scenarios:

```text
GET /api/v2/transcript-system/scenarios
```

Get one scenario:

```text
GET /api/v2/transcript-system/scenarios/{scenario_id}
```

Save scenario:

```text
PUT /api/v2/transcript-system/scenarios/{scenario_id}
```

Render student prompts:

```text
GET /api/v2/transcript-system/scenarios/{scenario_id}/prompts
```

Run readiness test:

```text
POST /api/v2/transcript-system/scenarios/{scenario_id}/test
```

Run selected-scenario TIL evaluation:

```text
POST /api/v2/transcript-system/scenarios/{scenario_id}/til-evaluation?reviewer_id=expert_reviewer_{scenario_id}
```

## 8. Recommended manual testing checklist

Test ít nhất 3 scenarios:

1. Một high school scenario.
2. Một college scenario.
3. Một university scenario.

Với mỗi scenario:

- đọc learning objectives;
- đọc misconception targets;
- chỉnh 1 student confidence;
- chỉnh 1 misconception_strength;
- chỉnh 1 prompt_instructions;
- chỉnh 1 row trong transcript table thật (`Turn | Name | Content`);
- save;
- run readiness test;
- nếu pass, bấm Proceed to TIL Evaluation;
- mở rendered prompt của student vừa chỉnh để kiểm tra prompt có đúng ý không;
- đọc transcript preview xem lesson arc có hợp lý không.

## 9. Next build sau khi Transcript System ổn

Sau khi bro review/chỉnh scenario, bước tiếp theo nên là:

1. Add “freeze scenario as benchmark transcript”.
2. Add scenario versioning: draft / frozen / expert-reviewed.
3. Add exporter sang golden benchmark format.
4. Add baseline vs TIL evaluator run từ scenario mới.
5. Add expert annotation form chi tiết hơn.
6. Sau đó mới quay lại rebuild Live Mode.

## 10. Important claim guardrail

Transcript System chỉ giúp tạo và kiểm soát classroom transcript để benchmark. Không claim rằng simulated students là real students. Claim đúng là:

```text
literature-informed / researcher-designed / optionally expert-informed classroom transcript scenarios
```

Claim chính của thesis vẫn là:

```text
fixed transcript benchmark + evidence-grounded evaluator + evidence verification + blinded expert review
```

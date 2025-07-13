from datetime import datetime, timedelta
import csv
import pyvips


class CalendarSVGGenerator:
    def __init__(self, cell_width=120, cell_height=140, header_height=40, margin=10, event_height=18):
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.header_height = header_height
        self.margin = margin
        self.event_height = event_height
        self.week_days = ['月', '火', '水', '木', '金', '土', '日']
        self.member_colors = {}
        self.events = []
        
    def get_week_range(self, target_date):
        """指定された日付を含む週の月曜日から日曜日までの日付を取得"""
        # 月曜日を週の始まりとする（0=月曜日）
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        
        week_dates = []
        for i in range(7):
            week_dates.append(monday + timedelta(days=i))
        
        return week_dates
    
    def get_four_week_range(self, today=None):
        """当日の週を含む4週間の日付範囲を取得（前1週間+当週+後2週間）"""
        if today is None:
            today = datetime.now().date()
        
        # 当日の週を取得
        current_week = self.get_week_range(today)
        
        # 前の週
        prev_week_start = current_week[0] - timedelta(days=7)
        prev_week = self.get_week_range(prev_week_start)
        
        # 後の2週間
        next_week1_start = current_week[0] + timedelta(days=7)
        next_week1 = self.get_week_range(next_week1_start)
        
        next_week2_start = current_week[0] + timedelta(days=14)
        next_week2 = self.get_week_range(next_week2_start)
        
        # 4週間分の日付をまとめる
        all_weeks = [prev_week, current_week, next_week1, next_week2]
        return all_weeks, today
    
    def load_events_from_csv(self, csv_file):
        """CSVファイルから予定を読み込む"""
        raw_events = []
        members = set()
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                
                for row in reader:
                    if len(row) >= 4:
                        start_date = datetime.strptime(row[0], '%Y/%m/%d').date()
                        end_date = datetime.strptime(row[1], '%Y/%m/%d').date()
                        member = row[2]
                        description = row[3]
                        
                        raw_events.append({
                            'start_date': start_date,
                            'end_date': end_date,
                            'member': member,
                            'description': description
                        })
                        members.add(member)
        except FileNotFoundError:
            print(f"Warning: {csv_file} not found")
            return
        
        # 同じ人で同じ期間の重複を削除（最後のデータを保持）
        self.events = self.remove_duplicate_events(raw_events)
        
        # メンバーの一覧を取得して色を割り当て
        unique_members = sorted(list(members))  # ソートして一定の順序に
        self.assign_member_colors(unique_members)
    
    def remove_duplicate_events(self, events):
        """Same person, same periodの重複を削除"""
        # (member, start_date, end_date)をキーとして最後のイベントを保持
        event_dict = {}
        for event in events:
            key = (event['member'], event['start_date'], event['end_date'])
            event_dict[key] = event  # 同じキーの場合、後のデータで上書き
        
        return list(event_dict.values())
    
    def assign_member_colors(self, members):
        """メンバーに区別しやすい色を割り当てる"""
        # 区別しやすい色を選択（銘明度と彩度を調整）
        colors = [
            '#ffb3ba',  # ライトピンク
            '#bae1ff',  # ライトブルー
            '#baffc9',  # ライトグリーン
            '#ffffba',  # ライトイエロー
            '#ffdfba',  # ライトオレンジ
            '#e0bbe4',  # ライトパープル
            '#d4d4aa',  # ライトオリーブ
            '#ffc9c9',  # ライトコーラル
            '#c9e4ff',  # ライトスカイブルー
            '#d4ffd4',  # ライトミント
            '#ffffe0',  # ライトクリーム
            '#ffe4e1',  # ライトローズ
            '#f0f8ff',  # アリスブルー
            '#f0fff0',  # ハニーデュー
            '#ffefd5',  # パパイヤホイップ
            '#e6e6fa',  # ラベンダー
            '#f5deb3',  # ウィート
            '#ffe4b5',  # モカシン
            '#dda0dd',  # プラム
            '#98fb98'   # ペールグリーン
        ]
        
        for i, member in enumerate(members):
            self.member_colors[member] = colors[i % len(colors)]
    
    def get_events_for_date_range(self, start_date, end_date):
        """指定された日付範囲の予定を取得"""
        return [event for event in self.events
                if not (event['end_date'] < start_date or event['start_date'] > end_date)]
    
    def calculate_event_layout(self, weeks):
        """予定のレイアウトを計算（重複回避）"""
        all_dates = []
        for week in weeks:
            all_dates.extend(week)
        
        start_date = all_dates[0]
        end_date = all_dates[-1]
        
        relevant_events = self.get_events_for_date_range(start_date, end_date)
        
        # 日付ごとのイベント配置を計算
        date_event_positions = {}
        for date in all_dates:
            date_event_positions[date] = []
        
        for event in relevant_events:
            # イベントの開始日から終了日まで、配置可能な位置を見つける
            event_dates = []
            current_date = max(event['start_date'], start_date)
            while current_date <= min(event['end_date'], end_date):
                event_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # 最適な配置位置を見つける
            position = 0
            while True:
                can_place = True
                for date in event_dates:
                    if position < len(date_event_positions[date]) and date_event_positions[date][position] is not None:
                        can_place = False
                        break
                
                if can_place:
                    # 配置を確定
                    for date in event_dates:
                        while len(date_event_positions[date]) <= position:
                            date_event_positions[date].append(None)
                        date_event_positions[date][position] = event
                    event['layout_position'] = position
                    break
                
                position += 1
        
        return date_event_positions
    
    def generate_svg(self, output_file="calendar.svg", today=None, csv_file="vacation.csv"):
        """4週間のカレンダーSVGを生成"""
        # CSVファイルから予定を読み込み
        self.load_events_from_csv(csv_file)
        weeks, today_date = self.get_four_week_range(today)
        
        # 予定のレイアウトを計算
        date_event_positions = self.calculate_event_layout(weeks)
        
        # 最大配置位置を計算してセルの高さを調整
        max_events = max([len(positions) for positions in date_event_positions.values()] + [0])
        if max_events > 0:
            self.cell_height = max(120, 60 + max_events * (self.event_height + 2))
        
        # SVGの全体サイズを計算
        total_width = 7 * self.cell_width + 2 * self.margin
        total_height = self.header_height + 4 * self.cell_height + 2 * self.margin  # ヘッダー行 + 4週間
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{total_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .header {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; text-anchor: middle; }}
            .date {{ font-family: Arial, sans-serif; font-size: 14px; text-anchor: middle; }}
            .month {{ font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; text-anchor: start; }}
            .day-number {{ font-family: Arial, sans-serif; font-size: 14px; text-anchor: end; }}
            .event {{ font-family: Arial, sans-serif; font-size: 10px; text-anchor: start; }}
            .event-rect {{ stroke: #666666; stroke-width: 0.5; }}
            .cell {{ fill: white; stroke: #cccccc; stroke-width: 1; }}
            .saturday {{ fill: #e3f2fd; }}
            .sunday {{ fill: #ffebee; }}
            .today {{ fill: #ffffa8; stroke: #cccccc; stroke-width: 1; }}
        </style>
    </defs>
    
    <!-- 背景 -->
    <rect width="{total_width}" height="{total_height}" fill="#fafafa"/>
'''
        
        # 曜日ヘッダーを描画
        y_offset = self.margin
        for i, day_name in enumerate(self.week_days):
            x = self.margin + i * self.cell_width
            svg_content += f'''
    <!-- 曜日ヘッダー: {day_name} -->
    <rect x="{x}" y="{y_offset}" width="{self.cell_width}" height="{self.header_height}" 
          class="cell" fill="#e0e0e0"/>
    <text x="{x + self.cell_width//2}" y="{y_offset + self.header_height//2 + 5}" 
          class="header">{day_name}</text>'''
        
        # 先にカレンダーのセルを全て描画
        for week_idx, week in enumerate(weeks):
            y = self.margin + self.header_height + week_idx * self.cell_height
            
            for day_idx, date in enumerate(week):
                x = self.margin + day_idx * self.cell_width
                
                # セルのスタイルを決定
                cell_class = "cell"
                if date == today_date:
                    cell_class += " today"
                elif day_idx == 5:  # 土曜日
                    cell_class += " saturday"
                elif day_idx == 6:  # 日曜日
                    cell_class += " sunday"
                
                # 月表示の判定（毎月1日のみ）
                month_text = ""
                if date.day == 1:
                    month_text = f'<text x="{x + 8}" y="{y + 20}" class="month">{date.month}月</text>'
                
                svg_content += f'''
    <!-- {date.strftime('%Y-%m-%d')} -->
    <rect x="{x}" y="{y}" width="{self.cell_width}" height="{self.cell_height}" 
          class="{cell_class}"/>
    {month_text}
    <text x="{x + self.cell_width - 8}" y="{y + 20}" 
          class="day-number">{date.day}</text>'''
        
        # カレンダー描画後にイベントの帯を描画
        for week_idx, week in enumerate(weeks):
            y = self.margin + self.header_height + week_idx * self.cell_height
            
            # この週のイベントを描画
            drawn_events = set()  # この週ですでに描画したイベントを記録（IDで管理）
            
            for day_idx, date in enumerate(week):
                x = self.margin + day_idx * self.cell_width
                
                if date in date_event_positions:
                    events_on_date = date_event_positions[date]
                    for pos, event in enumerate(events_on_date):
                        if event is not None:
                            event_id = (event['member'], event['start_date'], event['end_date'])
                            if event_id not in drawn_events:
                                # イベントがこの日に含まれるか確認
                                if event['start_date'] <= date <= event['end_date']:
                                    # この週でのイベント範囲を計算
                                    week_start = week[0]
                                    week_end = week[6]
                                    event_start_in_week = max(event['start_date'], week_start)
                                    event_end_in_week = min(event['end_date'], week_end)
                                    
                                    # イベントがこの週で開始する日のみ連続した帯を描画
                                    if event_start_in_week == date:
                                        drawn_events.add(event_id)  # 描画済みとして記録
                                        
                                        # 連続した帯の長さを計算
                                        start_day_idx = event_start_in_week.weekday()
                                        end_day_idx = event_end_in_week.weekday()
                                        event_length = end_day_idx - start_day_idx + 1
                                        
                                        event_width = event_length * self.cell_width - 4
                                        event_y = y + 30 + pos * (self.event_height + 2)
                                        member_color = self.member_colors.get(event['member'], '#f0f0f0')
                                        
                                        # イベントの表示テキスト
                                        if event['start_date'] == date or event_start_in_week == date:
                                            # イベントの開始日または週の開始日の場合テキストを表示
                                            if event['description'].strip():  # 説明がある場合
                                                display_text = f"{event['member']}: {event['description'][:15]}"
                                                if len(event['description']) > 15:
                                                    display_text += "..."
                                            else:  # 説明が空の場合
                                                display_text = event['member']
                                        else:
                                            # 継続部分の場合、テキストなし
                                            display_text = ""
                                        
                                        # テキストがある場合のみテキスト要素を追加
                                        text_element = ""
                                        if display_text:
                                            text_element = f'<text x="{x + 4}" y="{event_y + 12}" class="event">{display_text}</text>'
                                        
                                        svg_content += f'''
    <rect x="{x + 2}" y="{event_y}" width="{event_width}" height="{self.event_height}" 
          fill="{member_color}" class="event-rect"/>
    {text_element}'''
        
        svg_content += '''
</svg>'''
        
        # ファイルに書き込み
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return output_file
    
    def convert_svg_to_png(self, svg_file):
        """SVGファイルをPNGに変換（pyvipsを使用）"""
        png_file = svg_file.replace('.svg', '.png')
        
        try:
            # pyvipsでSVGをPNGに変換
            image = pyvips.Image.new_from_file(svg_file, dpi=300)
            image.write_to_file(png_file)
            print(f"PNG変換成功: {png_file}")
            return png_file
            
        except Exception as e:
            print(f"pyvips PNG変換エラー: {e}")
            return None
    
    def print_date_info(self, today=None):
        """デバッグ用：日付情報を表示"""
        weeks, today_date = self.get_four_week_range(today)
        print(f"基準日: {today_date}")
        print(f"4週間の日付範囲:")
        
        for week_idx, week in enumerate(weeks):
            week_type = ["前週", "当週", "次週1", "次週2"][week_idx]
            print(f"  {week_type}: {week[0]} ～ {week[-1]}")


def main():
    """メイン関数"""
    generator = CalendarSVGGenerator()
    
    # カレンダーSVGを生成
    output_file = generator.generate_svg(csv_file="vacation.csv")
    print(f"カレンダーSVGを生成しました: {output_file}")
    
    # PNGに変換
    png_file = generator.convert_svg_to_png(output_file)
    
    # 日付情報を表示
    generator.print_date_info()
    
    # 読み込んだ予定の情報を表示
    print(f"\n読み込んだ予定数: {len(generator.events)}")
    print(f"メンバー数: {len(generator.member_colors)}")
    for member, color in generator.member_colors.items():
        print(f"  {member}: {color}")


if __name__ == "__main__":
    main()
<script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
</script>
<script type="text/x-mathjax-config">
 MathJax.Hub.Config({
 tex2jax: {
 inlineMath: [['$', '$'] ],
 displayMath: [ ['$$','$$'], ["\\[","\\]"] ]
 }
 });
</script>
#使用技術
Python, Django, JavaScript, jQuery, Bootstrap5

マッチングについて

対戦希望者を詰める用のテーブルをデータベースに作っておく。
[対戦相手を探す]を押した際にAjaxでpost requestを投げて、そのユーザーをテーブルに追加し、同じテーブルからレートの近い範囲(現状は±10000)から相手をランダムに決定。
相手が見つかったら相手と自身を対戦希望者のテーブルから自身を削除する。
対戦相手は再帰関数で0.5秒ごとに探し、探している途中で自身が対戦希望者のテーブルから削除されていたら(相手側の処理で)終了する。
対戦相手が見つかったらやり取りをする部屋を作成し、そのURL情報をjsonでブラウザに返す。ブラウザはそのURLを受け取り、そこに移動する。

レート計算について

イロレーティングをデュエルリンクスのKCぽくなるようにアレンジしている。


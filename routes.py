from datetime import datetime

import numpy as np
from flask import *
from sklearn.metrics import confusion_matrix
from sqlalchemy import text
from pyecharts.charts import Bar
from pyecharts import options as opts
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from app import app, db
from models import ImportBatch, Wine


@app.route('/')
def index():
    db_ok = True
    db_error = None
    try:
        db.session.execute(text('SELECT 1'))
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    wine_count = Wine.query.count()
    batch_count = ImportBatch.query.count()
    latest_wine = Wine.query.order_by(Wine.id.desc()).first()
    latest_batch = latest_wine.import_batch if latest_wine else None
    

    return render_template(
        'index.html',
        now=datetime.now(),
        db_ok=db_ok,
        db_error=db_error,
        wine_count=wine_count,
        batch_count=batch_count,
        latest_wine=latest_wine,
        latest_batch=latest_batch,
    )

@app.route('/wines')
def wine_list():
    wines = Wine.query.order_by(Wine.id.desc()).all()
    return render_template('wine_list.html', wines=wines)


@app.route('/analysis')
def analysis_page():
    rows=Wine.query.with_entities(
        Wine.alcohol,
        Wine.malic_acid,
        Wine.color_intensity,
        Wine.target
        ).all()
    if not rows:
        return render_template(
            'analysis.html',
            accuracy=None,
            bar_chart=None,
            fi_chart=None,
            cm=None,
            labels=[0,1,2],
            msg="暂无数据，无法分析",
            
        )
        
    x=np.array([[i[0],i[1],i[2]] for i in rows],dtype=float)
    y=np.array([i[3] for i in rows],dtype=int)
    
    x_train,x_test,y_train,y_test=train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    model=DecisionTreeClassifier(random_state=42)
    model.fit(x_train,y_train)
    
    accuracy=float(model.score(x_test,y_test))
    
    y_pred=model.predict(x_test)
    cm=confusion_matrix(y_test,y_pred)
    cm_list=cm.tolist()
    
    acc_bar=(
        Bar(init_opts=opts.InitOpts(width="520px", height="320px"))
        .add_xaxis(["Accuracy"])
        .add_yaxis("Score",[round(accuracy,4)])
        .set_global_opts(
            title_opts=opts.TitleOpts(title="模型准确率"),
            yaxis_opts=opts.AxisOpts(min_=0, max_=1),
        )
    )
    feature_names=["alcohol","malic_acid","color_intensity"]
    importances=[round(float(i),4) for i in model.feature_importances_]
    
    fi_bar=(
        Bar(init_opts=opts.InitOpts(width="520px", height="320px"))
        .add_xaxis(feature_names)
        .add_yaxis("Importance",importances)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="特征重要性"),
            yaxis_opts=opts.AxisOpts(min_=0),
        )
    )
    
    return render_template(
        'analysis.html',
        accuracy=accuracy,
        bar_chart=acc_bar.render_embed(),
        fi_chart=fi_bar.render_embed(),
        cm=cm_list,
        labels=[0,1,2],
        msg=None,
    )

@app.route('/add',methods=['POST'])
def add_wine():
    source = (request.form.get('source') or '-').strip()
    if not source:
        abort(400)

    batch = (
        ImportBatch.query.filter_by(source=source)
        .order_by(ImportBatch.id.desc())
        .first()
    )
    if batch is None:
        batch = ImportBatch(source=source)
        db.session.add(batch)
        db.session.commit()

    try:
        alcohol = float(request.form['alcohol'])
        malic_acid = float(request.form['malic_acid'])
        color_intensity = float(request.form['color_intensity'])
        target = int(request.form['target'])
    except (KeyError, ValueError):
        abort(400)

    if target not in (0, 1, 2):
        abort(400)

    win = Wine(
        alcohol=alcohol,
        malic_acid=malic_acid,
        color_intensity=color_intensity,
        target=target,
        batch_id=batch.id,
    )
    db.session.add(win)
    db.session.commit()
    return redirect(url_for('wine_list'))


@app.route('/wines/<int:wine_id>/delete', methods=['POST'])
def delete_wine(wine_id: int):
    wine = Wine.query.get_or_404(wine_id)
    db.session.delete(wine)
    db.session.commit()
    return redirect(url_for('wine_list'))


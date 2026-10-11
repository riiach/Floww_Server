import os, tempfile, pathlib, subprocess
script = pathlib.Path(__file__).with_name('vercel-entrypoint.sh').read_text()
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d)
    (root/'entry.sh').write_text(script)
    java=root/'java'
    java.write_text('#!/bin/sh\nprintf "%s\\n" "$SPRING_DATASOURCE_URL" "$SPRING_FLYWAY_URL" "$FLOWW_DB_USER"\n')
    java.chmod(0o755)
    base={'PATH':d+':'+os.environ['PATH'], 'PGHOST':'ep-test-pooler.ap-southeast-1.aws.neon.tech','PGHOST_UNPOOLED':'ep-test.ap-southeast-1.aws.neon.tech','PGUSER':'fixture','PGPASSWORD':'fixture-only','PGDATABASE':'neondb'}
    def run(env):
        return subprocess.run(['sh',str(root/'entry.sh')],env=env,text=True,capture_output=True)
    p=run(base)
    assert p.returncode==0,p.stderr
    lines=p.stdout.splitlines()
    assert '-pooler.' in lines[0] and '-pooler.' not in lines[1]
    assert 'sslmode=verify-full' in lines[0] and 'DefaultJavaSSLFactory' in lines[1]
    assert 'prepareThreshold=0' in lines[0] and 'prepareThreshold=0' not in lines[1]
    for key,value in [('PGHOST_UNPOOLED',''),('PGUSER',''),('PGHOST','evil.example.com'),('PGHOST_UNPOOLED','ep-test-pooler.ap-southeast-1.aws.neon.tech'),('PGDATABASE','neondb?sslmode=disable')]:
        bad=dict(base);bad[key]=value
        assert run(bad).returncode!=0,key
    supabase={'PATH':base['PATH'],'FLOWW_DB_URL':'jdbc:postgresql://aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=verify-full','FLOWW_DB_USER':'fixture','FLOWW_DB_PASSWORD':'fixture-only'}
    p=run(supabase)
    assert p.returncode==0,p.stderr
    lines=p.stdout.splitlines()
    assert ':6543/' in lines[0] and ':5432/' in lines[1]
    print('PASS: Neon pooled/direct TLS mapping; 5 invalid configurations rejected; existing Supabase routing preserved.')
